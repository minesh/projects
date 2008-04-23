#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/errno.h>
#include <sys/wait.h>
#include <netinet/in.h>

#define PORT            9999
#define BACKLOG         5
#define MAX_BUF_SIZE    100

void sig_chld(int signo) {
    pid_t pid;
    int stat;

    while((pid = waitpid(WAIT_ANY, &stat, WNOHANG)) > 0)
        printf("child %d terminated\n", pid);
    return;
}

void str_echo(int sockfd) {
    int n;
    char line[MAX_BUF_SIZE];
    while(1) {
        if ((n = recv(sockfd, line, MAX_BUF_SIZE-1, 0)) == 0) {
            return;
        }
        line[n] = '\0';
        fflush(stdout);
        if (send(sockfd, line, n, 0) < 0) {
            perror("send");
        }
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

    /* Bind to any local interface */
    bzero(&serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    /* Allow the kernel to re-use the address */
    if (setsockopt(sock_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0) {
        perror("Error Setsockopt");
        exit(1);
    }


    if (bind(sock_fd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
        perror("ERROR Binding");
        exit(1);
    }

    /* Only allow BACKLOG amount of connections */
    if (listen(sock_fd, BACKLOG) < 0) {
        perror("ERROR Listening");
        exit(1);
    }

    /* Allow the kernel to re-use the address */
    if (setsockopt(sock_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0) {
        perror("Error Setsockopt");
        exit(1);
    }

    cli_len = sizeof(cli_addr);

    /* Set child signal handler */
    signal(SIGCHLD, sig_chld);

    /* Infinite loop */
    while(1) {
        if ((cli_fd = accept(sock_fd, (struct sockaddr *) &cli_addr,
                                                          &cli_len)) < 0) {
            /* Handle interrupted system calls */
            if (errno == EINTR) {
                continue;
            }
            else {
                perror("ERROR Accepting");
            }
        }
        printf("Server: got connection from %s\n",
                                                inet_ntoa(cli_addr.sin_addr));
        if (fork() == 0) {
            /* child doesn't need main socket */
            if (close(sock_fd) < 0) {
                perror("ERROR Closing FD");
                exit(1);
            }
            str_echo(cli_fd);
            /* Close cli_fd since we don't need it */
            if (close(cli_fd) < 0) {
                perror("ERROR Closing FD");
                exit(1);
            }
            exit(0);
        }
        if (close(cli_fd) < 0) {
            perror("ERROR Closing FD");
            exit(1);
        }
    }
    return 0;
}
