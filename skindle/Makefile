
OBJS=skindle.o md5.o sha1.o b64.o skinutils.o cbuf.o mobi.o tpz.o

CC=gcc
LD=gcc
EXE=skindle
EXTRALIBS=libz.a -lCrypt32 -lAdvapi32
CFLAGS=-mno-cygwin

#use the following to strip your binary
LDFLAGS=-s -mno-cygwin
#LDFLAGS=-mno-cygwin

all: $(EXE)

%.o: %.c
	$(CC) -c $(CFLAGS) -g $(INC) $< -o $@

$(EXE): $(OBJS)
	$(LD) $(LDFLAGS) -o $@ -g $(OBJS) $(EXTRALIBS)

clean:
	-@rm *.o
