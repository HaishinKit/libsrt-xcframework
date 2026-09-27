#include <libsrt/srt.h>
#include <openssl/crypto.h>
#include <arpa/inet.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>

static void check(bool ok, const char* message) {
    if (!ok) {
        std::fprintf(stderr, "%s: %s\n", message, srt_getlasterror_str());
        std::exit(1);
    }
}

static void configure(SRTSOCKET socket) {
    const char passphrase[] = "libsrt-openssl3-smoke-test";
    int keyLength = 32;
    int timeout = 5000;
    check(srt_setsockflag(socket, SRTO_PASSPHRASE, passphrase, sizeof(passphrase) - 1) == 0, "passphrase");
    check(srt_setsockflag(socket, SRTO_PBKEYLEN, &keyLength, sizeof(keyLength)) == 0, "AES-256");
    check(srt_setsockflag(socket, SRTO_RCVTIMEO, &timeout, sizeof(timeout)) == 0, "receive timeout");
    check(srt_setsockflag(socket, SRTO_SNDTIMEO, &timeout, sizeof(timeout)) == 0, "send timeout");
    check(srt_setsockflag(socket, SRTO_CONNTIMEO, &timeout, sizeof(timeout)) == 0, "connect timeout");
}

static void checkEncryption(SRTSOCKET socket, SRT_SOCKOPT option) {
    int state = 0;
    int size = sizeof(state);
    check(srt_getsockflag(socket, option, &state, &size) == 0 && state == SRT_KM_S_SECURED,
          "encrypted key state");
}

int main(int argc, char** argv) {
    const char* expectedVersion = argc > 1 ? argv[1] : "3.3.3";
    check(srt_getversion() == 0x010507, "SRT version");
    check(std::strcmp(OpenSSL_version(OPENSSL_VERSION_STRING), expectedVersion) == 0, "OpenSSL runtime version");
    check(srt_startup() == 0, "startup");
    SRTSOCKET listener = srt_create_socket();
    check(listener != SRT_INVALID_SOCK, "listener socket");
    configure(listener);
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    check(srt_bind(listener, reinterpret_cast<sockaddr*>(&address), sizeof(address)) == 0, "bind loopback");
    int size = sizeof(address);
    check(srt_getsockname(listener, reinterpret_cast<sockaddr*>(&address), &size) == 0, "bound port");
    check(srt_listen(listener, 1) == 0, "listen");
    const char payload[] = "SRT 1.5.7 with OpenSSL 3.x encrypted round trip";
    std::thread server([&] {
        SRTSOCKET peer = srt_accept(listener, nullptr, nullptr);
        check(peer != SRT_INVALID_SOCK, "accept");
        char buffer[1500];
        int received = srt_recvmsg(peer, buffer, sizeof(buffer));
        check(received == sizeof(payload) && std::memcmp(buffer, payload, sizeof(payload)) == 0, "decrypted payload");
        checkEncryption(peer, SRTO_RCVKMSTATE);
        check(srt_sendmsg(peer, buffer, received, -1, 1) == received, "encrypted reply");
        // Wait for acknowledgment so the reply is delivered before closing.
        check(srt_recvmsg(peer, buffer, sizeof(buffer)) == 1 && buffer[0] == '!', "reply acknowledgment");
        check(srt_close(peer) == 0, "close peer");
    });
    SRTSOCKET client = srt_create_socket();
    check(client != SRT_INVALID_SOCK, "client socket");
    configure(client);
    check(srt_connect(client, reinterpret_cast<sockaddr*>(&address), sizeof(address)) == 0, "connect");
    check(srt_sendmsg(client, payload, sizeof(payload), -1, 1) == sizeof(payload), "encrypted send");
    char reply[1500];
    int received = srt_recvmsg(client, reply, sizeof(reply));
    check(received == sizeof(payload) && std::memcmp(reply, payload, sizeof(payload)) == 0, "decrypted reply");
    checkEncryption(client, SRTO_SNDKMSTATE);
    checkEncryption(client, SRTO_RCVKMSTATE);
    check(srt_sendmsg(client, "!", 1, -1, 1) == 1, "acknowledge reply");
    server.join();
    check(srt_close(client) == 0, "close client");
    check(srt_close(listener) == 0, "close listener");
    check(srt_cleanup() == 0, "cleanup");
    std::puts("SRT 1.5.7 / OpenSSL 3.x: AES-256 encrypted loopback passed");
}
