
OBJS=skindle.o md5.o sha1.o b64.o

CC=gcc
LD=gcc
EXE=skindle
EXTRALIBS=-lCrypt32

#use the following to strip your binary
LDFLAGS=-s

all: $(EXE)

%.o: %.c
	$(CC) -c $(CFLAGS) $(INC) $< -o $@

$(EXE): $(OBJS)
	$(LD) $(LDFLAGS) -o $@ $(OBJS) $(EXTRALIBS)

clean:
	-@rm *.o
