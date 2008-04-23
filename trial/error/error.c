#include <errno.h>
#include <stdio.h>

int main(void) {
    errno = 1;
    printf("Errno is: %d\n", errno);
    return 0;
}
