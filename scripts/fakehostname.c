#include <string.h>
int gethostname(char *name, size_t len) {
    strncpy(name, "localhost", len);
    if (len > 0) name[len - 1] = '\0';
    return 0;
}
