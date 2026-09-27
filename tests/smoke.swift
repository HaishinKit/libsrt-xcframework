import libsrt
precondition(srt_getversion() == 0x010507)
precondition(srt_startup() == 0)
let socket = srt_create_socket()
precondition(socket != SRT_INVALID_SOCK)
precondition(srt_close(socket) == 0)
precondition(srt_cleanup() == 0)
print("libsrt 1.5.7: Swift import, link and lifecycle OK")
