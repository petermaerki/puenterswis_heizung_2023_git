#!/usr/bin/env python
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

# system packages
from ..typing import List, Optional, Tuple, Union

# custom packages
from .. import functions, const as Const
from ..common import CommonModbusFunctions, Request


class AsyncRequest(Request):
    """Asynchronously deconstruct request data received via TCP or Serial"""

    async def send_response(self,
                            values: Optional[list] = None,
                            signed: bool = True) -> None:
        """
        Send a response via the configured interface.

        :param      values:  The values
        :type       values:  Optional[list]
        :param      signed:  Indicates if signed values are used
        :type       signed:  bool
        """

        #print("sending async response...")
        await self._itf.send_response(slave_addr=self.unit_addr,
                                      function_code=self.function,
                                      request_register_addr=self.register_addr,
                                      request_register_qty=self.quantity,
                                      request_data=self.data,
                                      values=values,
                                      signed=signed,
                                      request=self)

    async def send_exception(self, exception_code: int) -> None:
        """
        Send an exception response.

        :param      exception_code:  The exception code
        :type       exception_code:  int
        """
        await self._itf.send_exception_response(slave_addr=self.unit_addr,
                                                function_code=self.function,
                                                exception_code=exception_code,
                                                request=self)


class CommonAsyncModbusFunctions(CommonModbusFunctions):
    """Common Async Modbus functions"""

    async def read_coils(self,
                         slave_addr: int,
                         starting_addr: int,
                         coil_qty: int) -> List[bool]:
        """@see CommonModbusFunctions.read_coils"""

        modbus_pdu = functions.read_coils(starting_address=starting_addr,
                                          quantity=coil_qty)

        response = await self._send_receive(slave_addr=slave_addr,
                                            modbus_pdu=modbus_pdu,
                                            count=True)

        status_pdu = functions.bytes_to_bool(byte_list=response,
                                             bit_qty=coil_qty)

        return status_pdu

    async def read_discrete_inputs(self,
                                   slave_addr: int,
                                   starting_addr: int,
                                   input_qty: int) -> List[bool]:
        """@see CommonModbusFunctions.read_discrete_inputs"""

        modbus_pdu = functions.read_discrete_inputs(
            starting_address=starting_addr,
            quantity=input_qty)

        response = await self._send_receive(slave_addr=slave_addr,
                                            modbus_pdu=modbus_pdu,
                                            count=True)

        status_pdu = functions.bytes_to_bool(byte_list=response,
                                             bit_qty=input_qty)

        return status_pdu

    async def read_holding_registers(self,
                                     slave_addr: int,
                                     starting_addr: int,
                                     register_qty: int,
                                     signed: bool = True) -> Tuple[int, ...]:
        """@see CommonModbusFunctions.read_holding_registers"""

        modbus_pdu = functions.read_holding_registers(
            starting_address=starting_addr,
            quantity=register_qty)

        response = await self._send_receive(slave_addr=slave_addr,
                                            modbus_pdu=modbus_pdu,
                                            count=True)

        register_value = functions.to_short(byte_array=response, signed=signed)

        return register_value

    async def read_input_registers(self,
                                   slave_addr: int,
                                   starting_addr: int,
                                   register_qty: int,
                                   signed: bool = True) -> Tuple[int, ...]:
        """@see CommonModbusFunctions.read_input_registers"""

        modbus_pdu = functions.read_input_registers(
            starting_address=starting_addr,
            quantity=register_qty)

        response = await self._send_receive(slave_addr=slave_addr,
                                            modbus_pdu=modbus_pdu,
                                            count=True)

        register_value = functions.to_short(byte_array=response, signed=signed)

        return register_value

    async def write_single_coil(self,
                                slave_addr: int,
                                output_address: int,
                                output_value: Union[int, bool]) -> bool:
        """@see CommonModbusFunctions.write_single_coil"""

        modbus_pdu = functions.write_single_coil(output_address=output_address,
                                                 output_value=output_value)

        response = await self._send_receive(slave_addr=slave_addr,
                                            modbus_pdu=modbus_pdu,
                                            count=False)

        if response is None:
            return False

        operation_status = functions.validate_resp_data(
            data=response,
            function_code=Const.WRITE_SINGLE_COIL,
            address=output_address,
            value=output_value,
            signed=False)

        return operation_status

    async def write_single_register(self,
                                    slave_addr: int,
                                    register_address: int,
                                    register_value: int,
                                    signed: bool = True) -> bool:
        """@see CommonModbusFunctions.write_single_register"""

        modbus_pdu = functions.write_single_register(
            register_address=register_address,
            register_value=register_value,
            signed=signed)

        response = await self._send_receive(slave_addr=slave_addr,
                                            modbus_pdu=modbus_pdu,
                                            count=False)

        if response is None:
            return False

        operation_status = functions.validate_resp_data(
            data=response,
            function_code=Const.WRITE_SINGLE_REGISTER,
            address=register_address,
            value=register_value,
            signed=signed)

        return operation_status

    async def write_multiple_coils(self,
                                   slave_addr: int,
                                   starting_address: int,
                                   output_values: list) -> bool:
        """@see CommonModbusFunctions.write_multiple_coils"""

        modbus_pdu = functions.write_multiple_coils(
            starting_address=starting_address,
            value_list=output_values)

        response = await self._send_receive(slave_addr=slave_addr,
                                            modbus_pdu=modbus_pdu,
                                            count=False)

        if response is None:
            return False

        operation_status = functions.validate_resp_data(
            data=response,
            function_code=Const.WRITE_MULTIPLE_COILS,
            address=starting_address,
            quantity=len(output_values))

        return operation_status

    async def write_multiple_registers(self,
                                       slave_addr: int,
                                       starting_address: int,
                                       register_values: List[int],
                                       signed: bool = True) -> bool:
        """@see CommonModbusFunctions.write_multiple_registers"""

        modbus_pdu = functions.write_multiple_registers(
            starting_address=starting_address,
            register_values=register_values,
            signed=signed)

        response = await self._send_receive(slave_addr=slave_addr,
                                            modbus_pdu=modbus_pdu,
                                            count=False)

        if response is None:
            return False

        operation_status = functions.validate_resp_data(
            data=response,
            function_code=Const.WRITE_MULTIPLE_REGISTERS,
            address=starting_address,
            quantity=len(register_values),
            signed=signed
        )

        return operation_status

    async def _send_receive(self,
                            slave_addr: int,
                            modbus_pdu: bytes,
                            count: bool) -> bytes:
        raise NotImplementedError("Must be overridden by subclass.")
