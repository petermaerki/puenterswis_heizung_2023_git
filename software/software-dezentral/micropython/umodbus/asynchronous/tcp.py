#!/usr/bin/env python3
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

# system packages
import struct
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# custom packages
from .modbus import AsyncModbus
from .common import AsyncRequest, CommonAsyncModbusFunctions
from .. import functions, const as Const
from ..common import ModbusException
from ..tcp import CommonTCPFunctions, TCPServer

# typing not natively supported on MicroPython
from ..typing import Optional, Tuple, List
from ..typing import Callable, Coroutine, Any, Dict


class AsyncModbusTCP(AsyncModbus):
    """
    Asynchronous equivalent of ModbusTCP class.

    @see ModbusTCP
    """
    def __init__(self, addr_list: Optional[List[int]] = None):
        super().__init__(
            # set itf to AsyncTCPServer object
            AsyncTCPServer(),
            addr_list
        )

    async def bind(self,
                   local_ip: str,
                   local_port: int = 502,
                   max_connections: int = 10) -> None:
        """@see ModbusTCP.bind"""

        await self._itf.bind(local_ip, local_port, max_connections)

    def get_bound_status(self) -> bool:
        """@see ModbusTCP.get_bound_status"""

        return self._itf.is_bound

    async def serve_forever(self) -> None:
        """@see AsyncTCPServer.serve_forever"""

        await self._itf.serve_forever()

    def server_close(self) -> None:
        """@see AsyncTCPServer.server_close"""

        self._itf.server_close()


class AsyncTCP(CommonTCPFunctions, CommonAsyncModbusFunctions):
    """
    Asynchronous equivalent of TCP class.

    @see TCP
    """
    def __init__(self,
                 slave_ip: str,
                 slave_port: int = 502,
                 timeout: float = 5.0):
        """
        Initializes an asynchronous TCP client.

        Warning: Client does not auto-connect on initialization,
        unlike the synchronous client. Call `connect()` before
        calling client methods.

        @see TCP
        """

        super().__init__(slave_ip=slave_ip,
                         slave_port=slave_port,
                         timeout=timeout)

        self._sock_reader: Optional[asyncio.StreamReader] = None
        self._sock_writer: Optional[asyncio.StreamWriter] = None
        self.protocol = self

    async def _send_receive(self,
                            slave_addr: int,
                            modbus_pdu: bytes,
                            count: bool) -> bytes:
        """@see TCP._send_receive"""

        mbap_hdr, trans_id = self._create_mbap_hdr(slave_addr=slave_addr,
                                                   modbus_pdu=modbus_pdu)

        if self._sock_writer is None or self._sock_reader is None:
            raise ValueError("_sock_writer is None, try calling bind()"
                             " on the server.")

        self._sock_writer.write(mbap_hdr + modbus_pdu)

        await self._sock_writer.drain()

        response = await self._sock_reader.read(256)

        modbus_data = self._validate_resp_hdr(response=response,
                                              trans_id=trans_id,
                                              slave_addr=slave_addr,
                                              function_code=modbus_pdu[0],
                                              count=count)

        return modbus_data

    async def connect(self) -> None:
        """@see TCP.connect"""

        if self._sock_writer is not None:
            # clean up old writer
            self._sock_writer.close()
            await self._sock_writer.wait_closed()

        self._sock_reader, self._sock_writer = \
            await asyncio.open_connection(self._slave_ip, self._slave_port)
        self.is_connected = True


class AsyncTCPServer(TCPServer):
    """
    Asynchronous equivalent of TCPServer class.

    @see TCPServer
    """
    def __init__(self, timeout: float = 5.0):
        super().__init__()
        self._is_bound: bool = False
        self._handle_request: Callable[[Optional[AsyncRequest]],
                                       Coroutine[Any, Any, bool]] = None
        self._unit_addr_list: Optional[List[int]] = None
        self._req_dict: Dict[AsyncRequest, Tuple[asyncio.StreamWriter,
                                                 int]] = {}
        self.timeout: float = timeout
        self._lock: asyncio.Lock = None

    async def bind(self,
                   local_ip: str,
                   local_port: int = 502,
                   max_connections: int = 1) -> None:
        """@see TCPServer.bind"""

        self._lock = asyncio.Lock()
        self.server = await asyncio.start_server(self._accept_request,
                                                 local_ip,
                                                 local_port)
        self._is_bound = True

    async def _send(self,
                    writer: asyncio.StreamWriter,
                    req_tid: int,
                    modbus_pdu: bytes,
                    slave_addr: int) -> None:
        """
        Asynchronous equivalent to TCPServer._send
        @see TCPServer._send for common (trailing) parameters

        :param      writer:      The socket output/writer
        :type       writer:      (u)asyncio.StreamWriter
        :param      req_tid:     The Modbus transaction ID
        :type       req_tid:     int
        """

        size = len(modbus_pdu)
        fmt = 'B' * size
        adu = struct.pack('>HHHB' + fmt,
                          req_tid,
                          0,
                          size + 1,
                          slave_addr,
                          *modbus_pdu)
        writer.write(adu)
        await writer.drain()

    async def send_response(self,
                            slave_addr: int,
                            function_code: int,
                            request_register_addr: int,
                            request_register_qty: int,
                            request_data: list,
                            values: Optional[list] = None,
                            signed: bool = True,
                            request: AsyncRequest = None) -> None:
        """
        Asynchronous equivalent to TCPServer.send_response
        @see TCPServer.send_response for common (leading) parameters

        :param      request:     The request to send a response for
        :type       request:     AsyncRequest
        """

        writer, req_tid = self._req_dict.pop(request)
        modbus_pdu = functions.response(function_code,
                                        request_register_addr,
                                        request_register_qty,
                                        request_data,
                                        values,
                                        signed)

        await self._send(writer, req_tid, modbus_pdu, slave_addr)

    async def send_exception_response(self,
                                      slave_addr: int,
                                      function_code: int,
                                      exception_code: int,
                                      request: AsyncRequest = None) -> None:
        """
        Asynchronous equivalent to TCPServer.send_exception_response
        @see TCPServer.send_exception_response for common (trailing) parameters

        :param      request:     The request to send a response for
        :type       request:     AsyncRequest
        """

        writer, req_tid = self._req_dict.pop(request)
        modbus_pdu = functions.exception_response(function_code,
                                                  exception_code)

        await self._send(writer, req_tid, modbus_pdu, slave_addr)

    async def _accept_request(self,
                              reader: asyncio.StreamReader,
                              writer: asyncio.StreamWriter) -> None:
        """
        Accept, read and decode a socket based request. Timeout and unit
        address list settings are based on values specified in constructor

        :param      reader:      The socket input/reader to read request from
        :type       reader:      (u)asyncio.StreamReader
        :param      writer:      The socket output/writer to send response to
        :type       writer:      (u)asyncio.StreamWriter
        """

        try:
            header_len = Const.MBAP_HDR_LENGTH - 1
            # TODO add "on_client_connected" and
            # "on_client_disconnected" callbacks for TCP
            # dest_addr = writer.get_extra_info('peername')

            while True:
                task = reader.read(128)
                if self.timeout is not None:
                    pass  # task = asyncio.wait_for(task, self.timeout)
                req: bytes = await task
                if len(req) == 0:
                    break

                req_header_no_uid = req[:header_len]
                req_tid, req_pid, req_len = struct.unpack('>HHH',
                                                          req_header_no_uid)
                req_uid_and_pdu = req[header_len:header_len + req_len]
                if (req_pid != 0):
                    raise ValueError(
                        "Modbus request error: expected PID of 0,"
                        " encountered {0} instead".format(req_pid))

                elif (self._unit_addr_list is None or
                      req_uid_and_pdu[0] in self._unit_addr_list):
                    async with self._lock:
                        # _handle_request = process(request)
                        if self._handle_request is None:
                            break
                        data = bytearray(req_uid_and_pdu)
                        request = AsyncRequest(self, data)
                        self._req_dict[request] = (writer, req_tid)
                        try:
                            await self._handle_request(request)
                        except ModbusException as err:
                            await self.send_exception_response(
                                request,
                                req[0],
                                err.function_code,
                                err.exception_code
                            )
        except Exception as err:
            if not isinstance(err, OSError):  # or err.errno != 104:
                print("{0}: ".format(type(err).__name__), err)
        finally:
            await self._close_writer(writer)

    def get_request(self,
                    unit_addr_list: Optional[List[int]] = None,
                    timeout: float = 0) -> None:
        """
        Unused function, kept for equivalent
        compatibility with synchronous version

        @see TCPServer.get_request
        """

        self._unit_addr_list = unit_addr_list
        self.timeout = timeout

    def set_params(self,
                   addr_list: Optional[List[int]],
                   req_handler: Callable[[Optional[AsyncRequest]],
                                         Coroutine[Any, Any, bool]]) -> None:
        """
        Used to set parameters such as the unit address
        list and the socket processing callback

        :param      addr_list:      The unit address list
        :type       addr_list:      List[int], optional
        :param      req_handler:    A callback that is responsible for parsing
                                    individual requests from a Modbus client
        :type       req_handler:    (Optional[AsyncRequest]) ->
                                        (() -> bool, async)
        """

        self._handle_request = req_handler
        self._unit_addr_list = addr_list

    async def _close_writer(self, writer: asyncio.StreamWriter) -> None:
        """
        Stops and closes the connection to a client.

        :param      writer:         The socket writer
        :type       writer:         (u)asyncio.StreamWriter
        """

        writer.close()
        await writer.wait_closed()

    async def serve_forever(self) -> None:
        """Waits for the server to close."""

        await self.server.wait_closed()

    def server_close(self) -> None:
        """Stops a running server."""

        if self._is_bound:
            self.server.close()
