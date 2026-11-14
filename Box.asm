// Box.asm
// Draws a black box starting at row K, 20 rows tall, and W words wide 
// when any keyboard key is pressed. Clears when released.
// K = 41

(CHECK_KEY)
    @KBD
    D=M
    @DRAW_BOX
    D;JNE
    @CLEAR_BOX
    0;JMP

(DRAW_BOX)
    @VAL
    M=-1
    @PROCESS
    0;JMP

(CLEAR_BOX)
    @VAL
    M=0
    @PROCESS
    0;JMP

(PROCESS)
    @20
    D=A
    @ROWS
    M=D

    // Compute SCREEN + 32 * K (for K=41, 32*41 = 1312)
    @SCREEN
    D=A
    @41
    D=D+A
    @ROW_PTR
    M=D

(ROW_LOOP)
    @ROWS
    D=M
    @CHECK_KEY
    D;JLE

    @ROW_PTR
    D=M
    @WORD_PTR
    M=D

    // Width W = (K mod 4) + 1 = (41 mod 4) + 1 = 1 + 1 = 2 words wide
    @2
    D=A
    @COLS
    M=D

(COL_LOOP)
    @COLS
    D=M
    @NEXT_ROW
    D;JLE

    @VAL
    D=M
    @WORD_PTR
    A=M
    M=D

    @WORD_PTR
    M=M+1
    @COLS
    M=M-1
    @COL_LOOP
    0;JMP

(NEXT_ROW)
    @32
    D=A
    @ROW_PTR
    M=M+D

    @ROWS
    M=M-1
    @ROW_LOOP
    0;JMP
