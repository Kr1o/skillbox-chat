#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)
        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")

                if self.login.lower() in map(lambda x:x.lower(), self.server.login):
                    self.existing_login(self.login)

                self.server.login.append(self.login)
                self.transport.write(
                    f"Привет, {self.login}!\n".encode()
                )
                self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.message_history.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    def existing_login(self, login):
        self.transport.write(
            f"Логин {login} занят, попробуйте другой\n".encode()
        )
        self.transport.close()

    def send_history(self):
        for msg in self.server.message_history[-10:]:
            self.transport.write(f"{msg}\n".encode())


class Server:
    clients: list
    login: list
    message_history: list

    def __init__(self):
        self.clients = []
        self.login = []
        self.message_history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
