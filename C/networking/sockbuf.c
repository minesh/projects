#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>

int main (void) {
    int sock_fd;
    int buf;
    unsigned int buf_size;

    buf_size = sizeof(unsigned int);

    sock_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (sock_fd < 0) {
        perror("Socket");
        exit(1);
    }
    if (getsockopt(sock_fd, SOL_SOCKET, SO_SNDBUF, &buf, &buf_size) < 0) {
        perror("Getsockopt");
        exit(1);
    }
    printf("Size of SO_SNDBUF is : %d\n", buf);
    return 0;
}
