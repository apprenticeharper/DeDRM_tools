/*
   Copyright 2010 BartSimpson aka skindle
   
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

#include <windows.h>
#include <Wincrypt.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>

#include "skinutils.h"

/* The kindle.info file created when you install KindleForPC is a set
 * of key:value pairs delimited by '{'.  The keys and values are encoded
 * in a variety of ways.  Keys are the mazama64 encoded md5 hash of the
 * key name, while values are the mazama64 encoding of the blob returned
 * by the Windows CryptProtectData function.  The use of CryptProtectData
 * is what locks things to a particular user/machine

 * kindle.info layout

 * Key:AbaZZ6z4a7ZxzLzkZcaqauZMZjZ_Ztz6   ("kindle.account.tokens")
 * Value: mazama64Encode(CryptProtectData(some sha1 hash))

 * Key:AsAWa4ZJAQaCZ7A3zrZSaZavZMarZFAw  ("kindle.cookie.item")
 * Value: mazama64Encode(CryptProtectData(base64(144 bytes of data)))

 * Key:ZHatAla4a-zTzWA-AvaeAvZQzKZ-agAz   ("eulaVersionAccepted")
 * Value: mazama64Encode(CryptProtectData(kindle version?))

 * Key:ZiajZga7Z9zjZRz7AfZ-zRzUANZNZJzP   ("login_date")
 * Value: mazama64Encode(CryptProtectData(registration date))

 * Key:ZkzeAUA-Z2ZYA2Z_ayA_ahZEATaEAOaG  ("kindle.token.item")
 * Value: mazama64Encode(CryptProtectData(multi-field crypto data))
 * {enc:xxx}{iv:xxx}{key:xxx}{name:xxx}{serial:xxx}
 * enc:base64(binary blob)
 * iv:base64(16 bytes)
 * key:base64(256 bytes)
 * name:base64("ADPTokenEncryptionKey")
 * serial:base64("1")

 * Key:aVzrzRAFZ7aIzmASZOzVzIAGAKawzwaU    ("login")
 * Value: mazama64Encode(CryptProtectData(your amazon email))

 * Key:avalzbzkAcAPAQA5ApZgaOZPzQZzaiaO   mazama64Encode(md5("MazamaRandomNumber"))
 * Value: mazama64Encode(CryptProtectData(mazama32Encode(32 bytes random data)))

 * Key:zgACzqAjZ2zzAmAJa6ZFaZALaYAlZrz-   ("kindle.key.item")
 * Value: mazama64Encode(CryptProtectData(RSA private key)) no password

 * Key:zga-aIANZPzbzfZ1zHZWZcA4afZMZcA_   ("kindle.name.info")
 * Value: mazama64Encode(CryptProtectData(your name))

 * Key:zlZ9afz1AfAVZjacaqa-ZHa1aIa_ajz7   ("kindle.device.info");
 * Value: mazama64Encode(CryptProtectData(the name of your kindle))
*/

char *kindleKeys[] = {
   "AbaZZ6z4a7ZxzLzkZcaqauZMZjZ_Ztz6", "kindle.account.tokens",
   "AsAWa4ZJAQaCZ7A3zrZSaZavZMarZFAw", "kindle.cookie.item",
   "ZHatAla4a-zTzWA-AvaeAvZQzKZ-agAz", "eulaVersionAccepted",
   "ZiajZga7Z9zjZRz7AfZ-zRzUANZNZJzP", "login_date",
   "ZkzeAUA-Z2ZYA2Z_ayA_ahZEATaEAOaG", "kindle.token.item",
   "aVzrzRAFZ7aIzmASZOzVzIAGAKawzwaU", "login",
   "avalzbzkAcAPAQA5ApZgaOZPzQZzaiaO", "MazamaRandomNumber",
   "zgACzqAjZ2zzAmAJa6ZFaZALaYAlZrz-", "kindle.key.item",
   "zga-aIANZPzbzfZ1zHZWZcA4afZMZcA_", "kindle.name.info",
   "zlZ9afz1AfAVZjacaqa-ZHa1aIa_ajz7", "kindle.device.info"
};

MapList *kindleMap;

unsigned short bswap_s(unsigned short s) {
   return (s >> 8) | (s << 8);
}

unsigned int bswap_l(unsigned int s) {
   unsigned int u = bswap_s(s);
   unsigned int l = bswap_s(s >> 16);
   return (u << 16) | l;
}

char *translateKindleKey(char *key) {
   int n = sizeof(kindleKeys) / sizeof(char*);
   int i;
   for (i = 0; i < n; i += 2) {
      if (strcmp(key, kindleKeys[i]) == 0) {
         return kindleKeys[i + 1];
      }
   }
   return NULL;
}

MapList *findNode(MapList *map, char *key) {
   MapList *l;
   for (l = map; l; l = l->next) {
      if (strcmp(key, l->key) == 0) {
         return l;
      }
   }
   return NULL;
}

MapList *findKindleNode(char *key) {
   return findNode(kindleMap, key);
}

char *getNodeValue(MapList *map, char *key) {
   MapList *l;
   for (l = map; l; l = l->next) {
      if (strcmp(key, l->key) == 0) {
         return l->value;
      }
   }
   return NULL;
}

char *getKindleValue(char *key) {
   return getNodeValue(kindleMap, key);
}

MapList *addMapNode(MapList *map, char *key, char *value) {
   MapList *ml;
   ml = findNode(map, key);
   if (ml) {
      free(ml->value);
      ml->value = value;
      return map;
   }
   else {
      ml = (MapList*)malloc(sizeof(MapList));
      ml->key = key;
      ml->value = value;
      ml->next = map;
      return ml;
   }
}

void dumpMap(MapList *m) {
   MapList *l;
   for (l = m; l; l = l->next) {
      fprintf(stderr, "%s:%s\n", l->key, l->value);
   }
}

void freeMap(MapList *m) {
   MapList *n;
   while (m) {
      n = m;
      m = m->next;
      free(n->key);
      free(n->value);
      free(n);
   }
}

void parseLine(char *line) {
   char *colon = strchr(line, ':');
   if (colon) {
      char *key, *value;
      int len = colon - line;
      key = (char*)malloc(len + 1);
      *colon++ = 0;
      strcpy(key, line);
      len = strlen(colon);
      value = (char*)malloc(len + 1);
      strcpy(value, colon);
      value[len] = 0;
      kindleMap = addMapNode(kindleMap, key, value);
   }
}

void dumpKindleMap() {
   dumpMap(kindleMap);
}

int buildKindleMap(char *infoFile) {
   int result = 0;
   struct stat statbuf;
   char ki[512];
   DWORD len = sizeof(ki);
   if (infoFile == NULL) {
      HKEY regkey;
      fprintf(stderr, "Attempting to locate kindle.info\n");
      if (RegOpenKey(HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders\\", &regkey) != ERROR_SUCCESS) {
         fprintf(stderr, "Unable to locate kindle.info, please specify path on command line\n");
         return result;      
      }
      
//      if (RegGetValue(regkey, "Local AppData", NULL, NULL, ki, &len) != ERROR_SUCCESS) {
      if (RegQueryValueEx(regkey, "Local AppData", NULL, NULL, ki, &len) != ERROR_SUCCESS) {
         RegCloseKey(regkey);
         fprintf(stderr, "Unable to locate kindle.info, please specify path on command line\n");
         return result;      
      }
      ki[len] = 0;
      strncat(ki, "\\Amazon\\Kindle For PC\\{AMAwzsaPaaZAzmZzZQzgZCAkZ3AjA_AY}\\kindle.info", sizeof(ki) - 1 - strlen(ki));
      infoFile = ki;      
      fprintf(stderr, "Found kindle.info location\n");
   }
   if (stat(infoFile, &statbuf) == 0) {
      FILE *fd = fopen(infoFile, "rb");
      char *infoBuf = (char*)malloc(statbuf.st_size + 1);
      infoBuf[statbuf.st_size] = 0;
      if (fread(infoBuf, statbuf.st_size, 1, fd) == 1) {
         char *end = infoBuf + statbuf.st_size;
         char *b = infoBuf, *e;
         while (e = strchr(b, '{')) {
            *e = 0;
            if ((e - b) > 2) {
               parseLine(b);
            }
            e++;
            b = e;
         }
         if (b < end) {
            parseLine(b);
         }
      }
      else {
         fprintf(stderr, "short read on info file\n");
      }
      free(infoBuf);
      fclose(fd);
      return 1;
   }
   return 0;
}

static unsigned int crc_table[256];

void png_crc_table_init() {
   unsigned int i;
   if (crc_table[255]) return;
   for (i = 0; i < 256; i++) {
      unsigned int n = i;
      unsigned int j;
      for (j = 0; j < 8; j++) {
         if (n & 1) {
            n = 0xEDB88320 ^ (n >> 1);
         }
         else {
            n >>= 1;
         }
      }
      crc_table[i] = n;
   }
}

unsigned int do_crc(unsigned char *input, unsigned int len) {
   unsigned int crc = 0;
   unsigned int i;
   png_crc_table_init();
   for (i = 0; i < len; i++) {
      unsigned int v = (input[i] ^ crc) & 0xff;
      crc = crc_table[v] ^ (crc >> 8);
   }
   return crc;
}

char *decodeString = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789";

void doPngDecode(unsigned char *input, unsigned int len, unsigned char *output) {
//   unsigned int crc_table[256];
   unsigned int crc, i, x = 0;
   unsigned int *out = (unsigned int*)output;
   crc = bswap_l(do_crc(input, len));
   memset(output, 0, 8);
   for (i = 0; i < len; i++) {
      output[x++] ^= input[i];
      if (x == 8) x = 0;
   }
   out[0] ^= crc;
   out[1] ^= crc;
   for (i = 0; i < 8; i++) {
      unsigned char v = output[i];
      output[i] = decodeString[((((v >> 5) & 3) ^ v) & 0x1F) + (v >> 7)];
   }
}

static char *string_32 = "n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M";
static char *string_64 = "AaZzB0bYyCc1XxDdW2wEeVv3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_";

char *mazamaEncode32(unsigned char *input, unsigned int len) {
   return mazamaEncode(input, len, 32);
}

char *mazamaEncode64(unsigned char *input, unsigned int len) {
   return mazamaEncode(input, len, 64);
}

char *mazamaEncode(unsigned char *input, unsigned int len, unsigned char choice) {
   unsigned int i;
   char *enc, *out;
   if (choice == 0x20) enc = string_32;
   else if (choice == 0x40) enc = string_64;
   else return NULL;
   out = (char*)malloc(len * 2 + 1);
   out[len * 2] = 0;
   for (i = 0; i < len; i++) {
      unsigned char v = input[i] + 128;
      unsigned char q = v / choice;
      unsigned char m = v % choice;
      out[i * 2] = enc[q];
      out[i * 2 + 1] = enc[m];
   }
   return out;
}

unsigned char *mazamaDecode(char *input, int *outlen) {
   unsigned char *out;
   int len = strlen(input);
   char *dec = NULL;
   int i, choice = 0x20;
   *outlen = 0;
   for (i = 0; i < 8 && i < len; i++) {
      if (*input == string_32[i]) {
         dec = string_32;
         break;
      }
   }
   if (dec == NULL) {
      for (i = 0; i < 4 && i < len; i++) {
         if (*input == string_64[i]) {
            dec = string_64;
            choice = 0x40;
            break;
         }
      }
   }
   if (dec == NULL) {
      return NULL;
   }
   out = (unsigned char*)malloc(len / 2 + 1);
   out[len / 2] = 0;
   for (i = 0; i < len; i += 2) {
      int q, m, v;
      char *p = strchr(dec, input[i]);
      if (p == NULL) break;
      q = p - dec;
      p = strchr(dec, input[i + 1]);
      if (p == NULL) break;
      m = p - dec;
      v = (choice * q + m) - 128;
      out[(*outlen)++] = (unsigned char)v;
   }
   return out;
}

#ifndef HEADER_MD5_H

void md5(unsigned char *in, int len, unsigned char *md) {
   MD5_CTX s;
   MD5_Init(&s);
	MD5_Update(&s, in, len);
	MD5_Final(md, &s);
}
#endif

#ifndef HEADER_SHA_H

void sha1(unsigned char *in, int len, unsigned char *md) {
   SHA_CTX s;
   SHA1_Init(&s);
	SHA1_Update(&s, in, len);
	SHA1_Final(md, &s);
}
#endif

char *getBookPid(unsigned char *keys, unsigned int klen, unsigned char *keysValue, unsigned int kvlen) {
   unsigned char *vsn, *username, *mrn_key, *kat_key, *pid;
   char drive[256];
   char name[256];
   DWORD nlen = sizeof(name);
   char *d;
   char volumeName[256];
   DWORD volumeSerialNumber;
   char fileSystemNameBuffer[256];
   char volumeID[32];
   unsigned char md5sum[MD5_DIGEST_LENGTH];
   unsigned char sha1sum[SHA_DIGEST_LENGTH];
   SHA_CTX sha1_ctx;
   char *mv;

   if (GetUserName(name, &nlen) == 0) {
      fprintf(stderr, "GetUserName failed\n");
      return NULL;
   }
   fprintf(stderr, "Using UserName = \"%s\"\n", name);

   d = getenv("SystemDrive");
   if (d) {
      strcpy(drive, d);
      strcat(drive, "\\");
   }
   else {
      strcpy(drive, "c:\\");
   }
   fprintf(stderr, "Using SystemDrive = \"%s\"\n", drive);
   if (GetVolumeInformation(drive, volumeName, sizeof(volumeName), &volumeSerialNumber,
                        NULL, NULL, fileSystemNameBuffer, sizeof(fileSystemNameBuffer))) {
      sprintf(volumeID, "%u", volumeSerialNumber);
   }
   else {
      strcpy(volumeID, "9999999999");
   }
   fprintf(stderr, "Using VolumeSerialNumber = \"%s\"\n", volumeID);
   MD5(volumeID, strlen(volumeID), md5sum);
   vsn = mazamaEncode(md5sum, MD5_DIGEST_LENGTH, 0x20);

   MD5(name, strlen(name), md5sum);
   username = mazamaEncode(md5sum, MD5_DIGEST_LENGTH, 0x20);

   MD5("MazamaRandomNumber", 18, md5sum);
   mrn_key = mazamaEncode(md5sum, MD5_DIGEST_LENGTH, 0x40);

   MD5("kindle.account.tokens", 21, md5sum);
   kat_key = mazamaEncode(md5sum, MD5_DIGEST_LENGTH, 0x40);

   SHA1_Init(&sha1_ctx);

   mv = getKindleValue(mrn_key);
   if (mv) {
      DATA_BLOB DataIn;
      DATA_BLOB DataOut;
      DataIn.pbData = mazamaDecode(mv, (int*)&DataIn.cbData);
      if (CryptUnprotectData(&DataIn, NULL, NULL, NULL, NULL, 1, &DataOut)) {
         char *devId = (char*)malloc(DataOut.cbData + 4 * MD5_DIGEST_LENGTH + 1);
         char *finalDevId;
         unsigned char pidbuf[10];
         
//         fprintf(stderr, "CryptUnprotectData success\n");
//         fwrite(DataOut.pbData, DataOut.cbData, 1, stderr);
//         fprintf(stderr, "\n");

         memcpy(devId, DataOut.pbData, DataOut.cbData);
         strcpy(devId + DataOut.cbData, vsn);
         strcat(devId + DataOut.cbData, username);

//         fprintf(stderr, "Computing sha1 over %d bytes\n", DataOut.cbData + 4 * MD5_DIGEST_LENGTH);
         sha1(devId, DataOut.cbData + 4 * MD5_DIGEST_LENGTH, sha1sum);
         finalDevId = mazamaEncode(sha1sum, SHA_DIGEST_LENGTH, 0x20);
//         fprintf(stderr, "finalDevId: %s\n", finalDevId);

         SHA1_Update(&sha1_ctx, finalDevId, strlen(finalDevId));

         pidbuf[8] = 0;
         doPngDecode(finalDevId, 4, (unsigned char*)pidbuf);
         fprintf(stderr, "Device PID: %s\n", pidbuf);

         LocalFree(DataOut.pbData);
         free(devId);
         free(finalDevId);
      }
      else {
         fprintf(stderr, "CryptUnprotectData failed, quitting\n");
         free(kat_key);
         free(mrn_key);
         return NULL;
      }

      free(DataIn.pbData);
   }
   else {
      fprintf(stderr, "Failed to find map node: %s\n", mrn_key);
   }

   mv = getKindleValue(kat_key);
   if (mv) {
      DATA_BLOB DataIn;
      DATA_BLOB DataOut;
      DataIn.pbData = mazamaDecode(mv, (int*)&DataIn.cbData);
      if (CryptUnprotectData(&DataIn, NULL, NULL, NULL, NULL, 1, &DataOut)) {
//         fprintf(stderr, "CryptUnprotectData success\n");
//         fwrite(DataOut.pbData, DataOut.cbData, 1, stderr);
//         fprintf(stderr, "\n");

         SHA1_Update(&sha1_ctx, DataOut.pbData, DataOut.cbData);

         LocalFree(DataOut.pbData);
      }
      else {
         fprintf(stderr, "CryptUnprotectData failed, quitting\n");
         free(kat_key);
         free(mrn_key);
         return NULL;
      }

      free(DataIn.pbData);
   }
   else {
      fprintf(stderr, "Failed to find map node: %s\n", kat_key);
   }

   SHA1_Update(&sha1_ctx, keys, klen);
   SHA1_Update(&sha1_ctx, keysValue, kvlen);
   SHA1_Final(sha1sum, &sha1_ctx);

   pid = (char*)malloc(SHA_DIGEST_LENGTH * 2);
   base64(sha1sum, SHA_DIGEST_LENGTH, pid);

   pid[8] = 0;

   free(mrn_key);
   free(kat_key);
   free(vsn);
   free(username);

   return pid;
}

static char *letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789";

int verifyPidChecksum(char *pid) {
   int l = strlen(letters);
   unsigned int crc = ~do_crc(pid, 8);
   unsigned char b;
   crc = crc ^ (crc >> 16);
   b = crc & 0xff;
   if (pid[8] != letters[((b / l) ^ (b % l)) % l]) return 0;
   crc >>= 8;
   b = crc & 0xff;
   if (pid[9] != letters[((b / l) ^ (b % l)) % l]) return 0;
   return 1;
}
