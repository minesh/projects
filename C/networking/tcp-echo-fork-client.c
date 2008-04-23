#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/errno.h>
#include <netinet/in.h>

#define PORT            9999
#define BACKLOG         5
#define MAX_BUF_SIZE    100

void str_cli(FILE *fp, int sockfd) {
    int n;
    char sendline[MAX_BUF_SIZE], recvline[MAX_BUF_SIZE];

    while(fgets(sendline, MAX_BUF_SIZE, fp) != NULL) {
        send(sockfd, sendline, strlen(sendline), 0);

        if ((n = recv(sockfd, recvline, MAX_BUF_SIZE, 0)) == 0) {
            printf("server closed connection\n");
            exit(1);
        }
        recvline[n] = '\0';
        fflush(stdout);
        fputs(recvline, stdout);
    }
}


int main(int argc, char **argv) {

    int sock_fd, cli_fd;
    int yes=1;
    int num_bytes;
    char buf[MAX_BUF_SIZE];
    unsigned int cli_len;
    struct sockaddr_in cli_addr, serv_addr;

    /* Create a server socket */
    if ((sock_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("ERROR Socket");
        exit(1);
    }

    /* Set destination port/IP */
    bzero(&serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    inet_pton(AF_INET, "192.168.1.77", &serv_addr.sin_addr);

    /* Allow the kernel to re-use the address */
    if (setsockopt(sock_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0) {
        perror("Error Setsockopt");
        exit(1);
    }

    /* Connect to remote */
    if (connect(sock_fd, (struct sockaddr *) &serv_addr, \
                                                    sizeof(serv_addr)) < 0) {
        perror("Error Connect");
        exit(1);
    }

    str_cli(stdin, sock_fd);

    return 0;
}
