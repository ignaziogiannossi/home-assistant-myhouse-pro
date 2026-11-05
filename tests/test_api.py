"""Protocol tests with synthetic data; no live network or Home Assistant needed."""
import asyncio
import importlib.util
import json
import ssl
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

SPEC = importlib.util.spec_from_file_location('myhouse_api', Path(__file__).parents[1] / 'custom_components/myhouse_pro/api.py')
api = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = api
SPEC.loader.exec_module(api)

DEVICE = api.Device('test-account', 'test-home', 'test-device', 'Thermostat', 'Example')
def detail(**changes):
    return {'eq_id': DEVICE.device_id, 'state': '1', 'temper_type': '0', 'tempera': '21.5', 'e_tempera': '22.5', 'humidity': '50', **changes}

def client():
    c = api.MyHouseClient(None)
    c.account_id = DEVICE.account_id
    c.devices = {DEVICE.device_id: DEVICE}
    return c

class Values(unittest.TestCase):
    def test_encryption_roundtrip(self):
        for value in ['', 'test-user@example.invalid', 'pàssword', '22.5']:
            self.assertEqual(api.decrypt(api.encrypt(value).encode()), value)

    def test_invalid_ciphertext(self):
        for value in [b'not base64!', b'', b'YWJj']:
            with self.assertRaises(api.ProtocolError): api.decrypt(value)

    def test_finite_numbers(self):
        for value in [None, True, False, 'nan', 'inf', '-inf', {}, [], 'bad', 10**1000]:
            self.assertIsNone(api.number(value))
        self.assertEqual(api.number('21.5'), 21.5)
        self.assertEqual(api.number(0), 0)

    def test_units(self):
        self.assertEqual(api.in_celsius(detail(), 'tempera'), 21.5)
        self.assertEqual(api.in_celsius(detail(temper_type='1', tempera='77'), 'tempera'), 25)
        for unit in [None, '', '9', False]:
            self.assertIsNone(api.in_celsius(detail(temper_type=unit), 'tempera'))
        self.assertIsNone(api.in_celsius(detail(tempera='nan'), 'tempera'))

    def test_identifiers(self):
        for value in [None, '', ' ', True, [], {}]:
            with self.assertRaises(api.ProtocolError): api.identifier(value)
        self.assertEqual(api.identifier(23), '23')

class Client(unittest.IsolatedAsyncioTestCase):
    async def test_login_and_discovery(self):
        c = api.MyHouseClient(None)
        c._post = AsyncMock(side_effect=[{'u_id':'test-account'}, [{'a_id':'test-home', 'a_name':'Example'}], [{'e_id':'2','eq_id':'test-device','eq_name':'Thermostat'}, {'e_id':'9','eq_id':'excluded'}]])
        self.assertEqual(await c.login('synthetic@example.invalid', 'synthetic'), 'test-account')
        self.assertEqual(await c.discover(), [DEVICE])

    async def test_login_clears_previous_identity(self):
        c=client(); c._post=AsyncMock(side_effect=api.AuthenticationError('rejected'))
        with self.assertRaises(api.AuthenticationError): await c.login('synthetic', 'synthetic')
        self.assertIsNone(c.account_id); self.assertEqual(c.devices,{})

    async def test_discovery_requires_login(self):
        with self.assertRaises(api.AuthenticationError): await api.MyHouseClient(None).discover()

    async def test_malformed_discovery(self):
        c=client(); c._post=AsyncMock(return_value={})
        with self.assertRaises(api.ProtocolError): await c.discover()

    async def test_wrong_device_read(self):
        c=client(); c._post=AsyncMock(return_value=detail(eq_id='another-device'))
        with self.assertRaises(api.ProtocolError): await c.read(DEVICE)

    async def test_ownership_blocks_read_and_write(self):
        c=client(); c.account_id='another-account'; c._post=AsyncMock()
        for command in [c.read(DEVICE),c.set_power(DEVICE,True),c.set_temperature(DEVICE,22,detail())]:
            with self.assertRaises(api.MyHouseError): await command
        c._post.assert_not_called()

    async def test_setpoint_validation(self):
        c=client(); c._post=AsyncMock()
        for value in [True, float('nan'), float('inf'), 4.5,35.5,22.1]:
            with self.assertRaises(api.MyHouseError): await c.set_temperature(DEVICE,value,detail())
        c._post.assert_not_called()
        await c.set_temperature(DEVICE,22.5,detail())
        c._post.assert_awaited_once_with('Index/edit_temper',{'eq_id':DEVICE.device_id,'temperature':'22.5'})

    async def test_fahrenheit_write(self):
        c=client();c._post=AsyncMock()
        await c.set_temperature(DEVICE,25,detail(temper_type='1'))
        self.assertEqual(c._post.call_args.args[1]['temperature'],'77.0')

    async def test_unknown_units_block_write(self):
        c=client();c._post=AsyncMock()
        for unit in [None,'9',False]:
            with self.assertRaises(api.ProtocolError): await c.set_temperature(DEVICE,22,detail(temper_type=unit))
        c._post.assert_not_called()

    async def test_offline_or_mismatched_device_blocks_temperature(self):
        c=client();c._post=AsyncMock()
        for data in [detail(state='3'),detail(eq_id='another-device')]:
            with self.assertRaises(api.MyHouseError): await c.set_temperature(DEVICE,22,data)
        c._post.assert_not_called()

    async def test_power_requires_boolean(self):
        c=client();c._post=AsyncMock()
        with self.assertRaises(api.MyHouseError): await c.set_power(DEVICE,'1')
        c._post.assert_not_called()
        await c.set_power(DEVICE,False)
        c._post.assert_awaited_once_with('Index/edit_switch',{'eq_id':DEVICE.device_id,'state':'2'})

class Response:
    def __init__(self, info=None, status=200, raw=None, result='succ'):
        self.status=status
        self.raw=raw if raw is not None else api.encrypt(json.dumps({'result':result,'info':info})).encode()
        self.content=self
    async def __aenter__(self): return self
    async def __aexit__(self,*args): return None
    async def read(self,size):
        chunk=self.raw[:size];self.raw=self.raw[size:];return chunk

class Session:
    def __init__(self,response): self.response=response;self.calls=[]
    def post(self,*args,**kwargs): self.calls.append((args,kwargs));return self.response

class Transport(unittest.IsolatedAsyncioTestCase):
    async def test_encrypted_request_and_no_redirects(self):
        s=Session(Response({'u_id':'test-account'}));c=api.MyHouseClient(s)
        self.assertEqual(await c.login('test@example.invalid','synthetic'), 'test-account')
        args,kwargs=s.calls[0]
        self.assertEqual(args[0],api.BASE_URL+'User/login?')
        self.assertFalse(kwargs['allow_redirects'])
        self.assertEqual(args[0], 'https://www.mycomforthouse.com/iotfront/api.php/User/login?')
        self.assertTrue(kwargs['ssl'].check_hostname)
        self.assertEqual(kwargs['ssl'].verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(api.decrypt(kwargs['data']['password'].encode()), 'synthetic')
        self.assertNotEqual(kwargs['data']['password'], 'synthetic')

    async def test_http_is_blocked_before_credentials_are_sent(self):
        s=Session(Response());c=api.MyHouseClient(s)
        with patch.object(api, 'BASE_URL', 'http://www.mycomforthouse.com:8080/iotfront/api.php/'):
            with self.assertRaises(api.MyHouseError): await c.login('synthetic', 'synthetic')
        self.assertEqual(s.calls, [])

    async def test_certificate_failure_never_falls_back_or_retries(self):
        class Untrusted:
            def __init__(self): self.calls=[]
            def post(self, *args, **kwargs):
                self.calls.append((args, kwargs))
                raise ssl.SSLCertVerificationError('untrusted certificate; private-data')
        s=Untrusted();c=api.MyHouseClient(s)
        with self.assertRaises(api.MyHouseError) as result: await c.login('synthetic', 'synthetic')
        self.assertEqual(len(s.calls), 1)
        self.assertTrue(s.calls[0][0][0].startswith('https://'))
        self.assertNotIn('private-data', str(result.exception))

    async def test_redirects_are_rejected_without_resending_credentials(self):
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                s=Session(Response(status=status));c=api.MyHouseClient(s)
                with self.assertRaises(api.MyHouseError): await c.login('synthetic', 'synthetic')
                self.assertEqual(len(s.calls), 1)
                self.assertFalse(s.calls[0][1]['allow_redirects'])

    async def test_read_and_write_use_verified_https(self):
        s=Session(Response(detail()));c=api.MyHouseClient(s)
        c.account_id=DEVICE.account_id;c.devices={DEVICE.device_id:DEVICE}
        await c.read(DEVICE)
        s.response=Response({})
        await c.set_power(DEVICE, True)
        s.response=Response({})
        await c.set_temperature(DEVICE, 22, detail())
        self.assertEqual(len(s.calls), 3)
        for args, kwargs in s.calls:
            self.assertTrue(args[0].startswith('https://www.mycomforthouse.com/'))
            self.assertTrue(kwargs['ssl'].check_hostname)
            self.assertEqual(kwargs['ssl'].verify_mode, ssl.CERT_REQUIRED)
            self.assertFalse(kwargs['allow_redirects'])

    async def test_rejected_login(self):
        c=api.MyHouseClient(Session(Response(result='fail')))
        with self.assertRaises(api.AuthenticationError): await c.login('synthetic','synthetic')

    async def test_http_error_excludes_body(self):
        c=api.MyHouseClient(Session(Response(status=503,raw=b'private-data')))
        with self.assertRaises(api.MyHouseError) as result: await c.login('synthetic','synthetic')
        self.assertNotIn('private-data',str(result.exception))
        self.assertIn('503',str(result.exception))

    async def test_oversized_response(self):
        c=api.MyHouseClient(Session(Response(raw=b'x'*(api.MAX_RESPONSE+1))))
        with self.assertRaises(api.ProtocolError): await c.login('synthetic','synthetic')

    async def test_invalid_json(self):
        c=api.MyHouseClient(Session(Response(raw=api.encrypt('not-json').encode())))
        with self.assertRaises(api.ProtocolError): await c.login('synthetic','synthetic')

    async def test_invalid_shape(self):
        c=api.MyHouseClient(Session(Response(raw=api.encrypt('[]').encode())))
        with self.assertRaises(api.ProtocolError): await c.login('synthetic','synthetic')

    async def test_transport_exception_sanitized(self):
        class Broken:
            def post(self,*args,**kwargs): raise RuntimeError('password=private-data')
        c=api.MyHouseClient(Broken())
        with self.assertRaises(api.MyHouseError) as result: await c.login('synthetic','synthetic')
        self.assertNotIn('private-data',str(result.exception))
        self.assertTrue(result.exception.__suppress_context__)

    async def test_timeout_sanitized(self):
        class Slow(Response):
            async def read(self,size): await asyncio.sleep(1)
        c=api.MyHouseClient(Session(Slow()))
        with patch.object(api,'TIMEOUT',0.001):
            with self.assertRaises(api.MyHouseError): await c.login('synthetic','synthetic')

class Commands(unittest.IsolatedAsyncioTestCase):
    def controller(self,values):
        c=client();c.read=AsyncMock(side_effect=values);c.set_temperature=AsyncMock();c.set_power=AsyncMock()
        return c,api.DeviceController(c,DEVICE,delay=0,attempts=2)

    async def test_temperature_confirmed_after_poll(self):
        c,ctrl=self.controller([detail(),detail(),detail(e_tempera='23.0')])
        self.assertEqual((await ctrl.command(temperature=23))['e_tempera'],'23.0')
        c.set_temperature.assert_awaited_once(); self.assertEqual(c.read.await_count,3)

    async def test_power_confirmed(self):
        c,ctrl=self.controller([detail(),detail(state='2')])
        self.assertEqual((await ctrl.command(power=False))['state'],'2')
        c.set_power.assert_awaited_once_with(DEVICE,False)

    async def test_unconfirmed_write_is_not_repeated(self):
        c,ctrl=self.controller([detail(),detail(),detail()])
        with self.assertRaises(api.CommandNotConfirmed): await ctrl.command(temperature=23)
        c.set_temperature.assert_awaited_once()

    async def test_offline_blocks_all_commands(self):
        c,ctrl=self.controller([detail(state='3')])
        with self.assertRaises(api.MyHouseError): await ctrl.command(power=True)
        c.set_power.assert_not_called()

    async def test_offline_readback_does_not_confirm(self):
        c,ctrl=self.controller([detail(),detail(state='3',e_tempera='23'),detail(state='3',e_tempera='23')])
        with self.assertRaises(api.CommandNotConfirmed): await ctrl.command(temperature=23)

    async def test_exactly_one_command(self):
        c,ctrl=self.controller([])
        for kwargs in [{},{'temperature':22,'power':True}]:
            with self.assertRaises(api.MyHouseError): await ctrl.command(**kwargs)
        c.read.assert_not_called()

    async def test_concurrent_commands_are_serialized(self):
        c=client();c.read=AsyncMock(side_effect=[detail(),detail(state='2'),detail(state='2'),detail(state='1')]);c.set_power=AsyncMock()
        ctrl=api.DeviceController(c,DEVICE,delay=0,attempts=1)
        values=await asyncio.gather(ctrl.command(power=False),ctrl.command(power=True))
        self.assertEqual([x['state'] for x in values],['2','1'])
        self.assertEqual([x.args[1] for x in c.set_power.call_args_list],[False,True])
