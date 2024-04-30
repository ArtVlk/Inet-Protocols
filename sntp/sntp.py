from typing import Tuple, override
import asyncio
import struct
import json
import time


class SNTPProtocol(asyncio.DatagramProtocol):

    def __init__(self, time_shift: int = 0):
        super().__init__()
        self.transport: asyncio.DatagramTransport = None
        self.package_format = struct.Struct('!BBBBIIIQQQQ')
        self.ntp_offset = 2208988800
        self.time_shift = time_shift

    @override
    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport

    def count_time(self):
        return (int(time.time() +
                    self.ntp_offset
                    + self.time_shift)
                * 2 ** 32)

    def create_package(self, data: bytes):
        received_packet = self.package_format.unpack(data)
        reply_package = self.package_format.pack(
            0b00100100, 1, 0, 0, 0, 0, 0, 0,
            received_packet[10], self.count_time(),
            self.count_time()
        )
        return reply_package

    @override
    def datagram_received(self, data: bytes, addr: tuple):
        try:
            received_package = self.package_format.unpack(data)
            print(f'Получен SNTP пакет от: {addr}')
            reply = self.create_package(data)
            self.transport.sendto(reply, addr)
        except struct.error:
            print(f'Некорректный формат SNTP пакета от: {addr}')


async def main():
    with open('config.json', mode='rb') as file:
        data = json.load(file)
        address: Tuple[str, int] = data['host'], data['port']
        shift: int = data['shift']

    loop = asyncio.get_event_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: SNTPProtocol(shift),
        local_addr=address)

    try:
        await asyncio.sleep(3600)

    except asyncio.CancelledError:

        print('Сервер отключён.')

    finally:
        transport.close()


if __name__ == '__main__':
    asyncio.run(main())
