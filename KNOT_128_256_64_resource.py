
from projectq.ops import H, CNOT, Measure, Toffoli, X, All
from projectq import MainEngine
from projectq.backends import ResourceCounter, ClassicalSimulator

from projectq.meta import Loop, Compute, Uncompute, Control

def KNOT(eng):

    key = eng.allocate_qureg(128)
    nonce = eng.allocate_qureg(128)

    Round_constant_XOR2(eng, key, 0x0f0e0d0c0b0a09080706050403020100)
    Round_constant_XOR2(eng, nonce, 0x0f0e0d0c0b0a09080706050403020100)

    AD_size = 32 # Multiples of 8-qubit
    P_size = 32  # Multiples of 8-qubit

    input_AD = eng.allocate_qureg(AD_size)
    input_P = eng.allocate_qureg(P_size)

    Round_constant_XOR2(eng, input_AD, 0x03020100)
    Round_constant_XOR2(eng, input_P, 0x03020100)

    # Padding
    u = UPad(eng, AD_size)
    v = UPad(eng, P_size)

    # Allocate C according to P_size
    if(v!= 0):
        C = eng.allocate_qureg((v-1)*64 + (P_size%64))

    # Initialization
    print('Initialization')
    S = []
    for i in range(128):
        S.append(nonce[i])
    for i in range(128):
        S.append(key[i])

    Round52(eng, S)

    # Processing Associated Data
    print('Processing AD')
    if (u != 0):
        Processing_AD(eng, S, input_AD, u, AD_size)
    else:
        X | S[-1]

    #Encryption
    if (v != 0):
        print('Encryption')
        Encryption(eng, input_P, S, C, v, P_size)

    #Finalization
    print('Finalization')
    Round32(eng, S) # S[0~127] becomes Tag


def UPad(eng, size):

    padsize = 0

    if(size > 0):
        padsize  = 64 - (size % 64)

    return int((size + padsize) / 64)


# nr0 : 52, nr : 28,  nrf :32

def Round52(eng, b):

    rc = [0x1, 0x2, 0x4, 0x8, 0x10, 0x21, 0x3, 0x6, 0xc, 0x18, 0x31, 0x22, 0x5, 0xa, 0x14, 0x29,
              0x13, 0x27, 0xf, 0x1e, 0x3d, 0x3a, 0x34, 0x28, 0x11, 0x23, 0x7, 0xe, 0x1c, 0x39, 0x32,
              0x24, 0x9, 0x12, 0x25, 0xb, 0x16, 0x2d, 0x1b, 0x37, 0x2e, 0x1d, 0x3b, 0x36, 0x2c, 0x19,
              0x33, 0x26, 0xd, 0x1a, 0x35, 0x2a, 0x15, 0x2b, 0x17, 0x2f, 0x1f, 0x3f, 0x3e, 0x3c, 0x38,
              0x30, 0x20]

    for i in range(52):
        Round_constant_XOR(eng, b, rc[i])
        SubColumn(eng, b)
        #ShiftRow(eng, b)
        print('Round',i)

def Round28(eng, b):

    rc = [0x1, 0x2, 0x4, 0x8, 0x10, 0x21, 0x3, 0x6, 0xc, 0x18, 0x31, 0x22, 0x5, 0xa, 0x14, 0x29,
              0x13, 0x27, 0xf, 0x1e, 0x3d, 0x3a, 0x34, 0x28, 0x11, 0x23, 0x7, 0xe, 0x1c, 0x39, 0x32,
              0x24, 0x9, 0x12, 0x25, 0xb, 0x16, 0x2d, 0x1b, 0x37, 0x2e, 0x1d, 0x3b, 0x36, 0x2c, 0x19,
              0x33, 0x26, 0xd, 0x1a, 0x35, 0x2a, 0x15, 0x2b, 0x17, 0x2f, 0x1f, 0x3f, 0x3e, 0x3c, 0x38,
              0x30, 0x20]

    for i in range(28):
        Round_constant_XOR(eng, b, rc[i])
        SubColumn(eng, b)
        #ShiftRow(eng, b)
        print('Round',i)

def Round32(eng, b):

    rc = [0x1, 0x2, 0x4, 0x8, 0x10, 0x21, 0x3, 0x6, 0xc, 0x18, 0x31, 0x22, 0x5, 0xa, 0x14, 0x29,
              0x13, 0x27, 0xf, 0x1e, 0x3d, 0x3a, 0x34, 0x28, 0x11, 0x23, 0x7, 0xe, 0x1c, 0x39, 0x32,
              0x24, 0x9, 0x12, 0x25, 0xb, 0x16, 0x2d, 0x1b, 0x37, 0x2e, 0x1d, 0x3b, 0x36, 0x2c, 0x19,
              0x33, 0x26, 0xd, 0x1a, 0x35, 0x2a, 0x15, 0x2b, 0x17, 0x2f, 0x1f, 0x3f, 0x3e, 0x3c, 0x38,
              0x30, 0x20]

    for i in range(32):
        Round_constant_XOR(eng, b, rc[i])
        SubColumn(eng, b)
        #ShiftRow(eng, b)
        print('Round',i)

def Round_constant_XOR(eng, k, rc):
    for i in range(6):
        if(rc >> i & 1):
             X | k[i]

def SubColumn(eng, b):
    b_column = []

    for i in range(64):
        b_column.append(b[i])
        b_column.append(b[64 + i])
        b_column.append(b[128+i])
        b_column.append(b[192+i])

    for i in range(64):
        Sbox_LIGHTER_R(eng, b_column[i*4:(i*4)+4])

def Sbox_LIGHTER_R(eng, b):

    X | b[0]
    Toffoli | (b[0], b[1], b[2])
    Toffoli | (b[1], b[2], b[0])

    CNOT | (b[2], b[3])
    CNOT | (b[3], b[1])
    CNOT | (b[1], b[0])

    Toffoli | (b[0], b[2], b[1])
    Toffoli | (b[0], b[1], b[2])


    #b2 = b0
    #b1 = b2
    #b0 = b1

    #Swap | (b[2], b[0])
    #Swap | (b[0], b[1])

def ShiftRow(eng, b):
    '''
    for j in range(1):  # Row1 ≪ 1
        for i in range(63):
            Swap | (b[127-i], b[126-i])

    for j in range(8):  # Row2 ≪ 8
        for i in range(63):
            Swap | (b[191-i], b[190-i])

    for j in range(25):  # # Row3 ≪ 25
        for i in range(63):
            Swap | (b[255-i], b[254-i])
    '''
def Processing_AD(eng, S, AD, u, AD_size):

    # AD -> 64-bit i.e (1 block case)
    for i in range(u):
        if(i == u-1):
            for z in range(AD_size % 64):
                CNOT | (AD[i * 64 + z], S[z])
            X | S[(AD_size) % 64]
        else :
            for j in range(64):
                CNOT | (AD[i*64 + j], S[j])
        Round28(eng, S)

    X | S[-1]

def Encryption(eng, P, S, C, v, P_size):

    for j in range(v-1):
        for i in range(64):
            CNOT | (P[64*j + i], S[i])
        # Copy C
        for i in range(64):
            CNOT | (S[i], C[64*j + i])

        Round28(eng, S)

    #last
    for i in range(P_size % 64):
        CNOT | (P[64*(v-1) + i], S[i])
    X | S[(P_size) % 64]

    # Copy C
    for i in range(P_size % 64):
        CNOT | (S[i], C[64*(v-1) + i])


def Round_constant_XOR(eng, k, rc):
    for i in range(8):
        if(rc >> i & 1):
             X | k[i]

def Round_constant_XOR2(eng, k, rc):
    for i in range(128):
        if(rc >> i & 1):
             X | k[i]

################ Resource analysis ###############
Resource = ResourceCounter()
eng = MainEngine(Resource)
(KNOT(eng))
print(Resource)
eng.flush
