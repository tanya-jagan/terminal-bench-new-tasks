// NOT included in binary

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>

static int b36val(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'Z') return c - 'A' + 10;
    return -1;
}

static uint32_t hash_username(const char *username) {
    uint32_t h = 0;
    for (const char *p = username; *p; p++) {
        h = (h * 31u + (unsigned char)*p);
    }
    return h;
}

static int validate(const char *username, const char *key) {
    /* Step 1: strip dashes, validate format */
    char s[21];
    int si = 0;
    int group = 0, in_group = 0;

    for (const char *p = key; *p; p++) {
        if (*p == '-') {
            if (in_group != 5) return 0;
            group++;
            in_group = 0;
            if (group > 3) return 0;
        } else {
            char c = toupper((unsigned char)*p);
            if (b36val(c) < 0) return 0;
            s[si++] = c;
            in_group++;
            if (si > 20) return 0;
        }
    }
    if (si != 20 || in_group != 5) return 0;
    s[20] = '\0';

    /* Step 2: username hash */
    uint32_t H = hash_username(username);

    /* Step 3: decode base-36 -> 64-bit */
    uint64_t K = 0;
    for (int i = 0; i < 20; i++) {
        K = K * 36 + b36val(s[i]);
    }

    /* Step 4: extract fields */
    uint32_t version   = (K >> 60) & 0xFULL;
    uint32_t checksum  = (K >> 48) & 0xFFFULL;
    uint32_t user_hash = (K >> 16) & 0xFFFFFFFFULL;
    uint32_t serial    = K & 0xFFFFULL;

    /* Step 5: validate */
    if (version != 3) return 0;
    if (user_hash != H) return 0;
    if (serial == 0) return 0;
    uint32_t expected_cs = (uint32_t)(((H ^ serial ^ 0xA5F3u) * 0x9E37u) & 0xFFFu);
    if (checksum != expected_cs) return 0;

    return 1;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <username> <license-key>\n", argv[0]);
        fprintf(stderr, "Example: %s tb3testuser AAAAA-BBBBB-CCCCC-DDDDD\n", argv[0]);
        return 2;
    }

    const char *username = argv[1];
    const char *key      = argv[2];

    if (validate(username, key)) {
        printf("License valid.\n");
        return 0;
    } else {
        printf("License invalid.\n");
        return 1;
    }
}

