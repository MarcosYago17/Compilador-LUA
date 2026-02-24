.data
x: .word 0
y: .word 0
str_0: .asciiz "X e menor que Y\n"
newline: .asciiz "\n"
str_1: .asciiz "X e maior ou igual\n"
i: .word 0

.text
.globl main
main:
    li $t0, 10  # Carrega numero
    sw $t0, x  # Salva em x
    li $t1, 20  # Carrega numero
    sw $t1, y  # Salva em y
    lw $t2, x  # Le variavel x
    lw $t3, y  # Le variavel y
    slt $t4, $t2, $t3
    beq $t4, $zero, Else0
    la $t5, str_0  # Carrega endereco da string
    move $a0, $t5
    li $v0, 1  # Syscall print_int
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    j FimIf1
Else0:
    la $t7, str_1  # Carrega endereco da string
    move $a0, $t7
    li $v0, 1  # Syscall print_int
    syscall
    la $a0, newline
    li $v0, 4
    syscall
FimIf1:
    li $t9, 1  # Carrega numero
    sw $t9, i  # Inicia i
ForInicio2:
    lw $t0, i
    li $t1, 5  # Carrega numero
    bgt $t0, $t1, ForFim3
    lw $t2, i  # Le variavel i
    move $a0, $t2
    li $v0, 1  # Syscall print_int
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    li $t4, 1  # Carrega numero
    lw $t0, i
    add $t0, $t0, $t4 # Incrementa for
    sw $t0, i
    j ForInicio2
ForFim3:
    li $v0, 10
    syscall
