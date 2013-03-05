#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include "rtp.h"

void usage(void) {
   printf("Usage:\n");
   printf("-h <hostname>\n");
   printf("-p <port number>\n");
}
int main(int argc, char **argv) {
   printf("Starting %s...\n", *argv);
   int c;
   uint16_t port;
   char *hostname = NULL;
   while ((c = getopt(argc, argv, "h:p:")) != -1) {
      switch(c) {
         case 'h':
            printf("option h: %s\n", optarg);
            hostname = optarg;
            break;
         case 'p':
            printf("option p: %u\n", atoi(optarg));
            port = atoi(optarg);
            break;
         case '?':
            usage();
            if (c == 'h' || c == 'p') {
               fprintf(stderr, "option: '%c' requires an argument, exiting\n",
                      optopt);
            } else {
               fprintf(stderr, "Unknown option: '%c', exiting\n", optopt);
            }
            return 1;
         default:
            fprintf(stderr, "ERROR: Should never reach here: '%c'\n", optopt);
            exit(EXIT_FAILURE);
      }
   }
   return 0;
}
