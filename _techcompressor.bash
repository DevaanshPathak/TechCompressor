#!/usr/bin/env bash
# Bash completion for techcompressor/techcmp

_techcompressor() {
    local cur prev opts commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main options
    opts="--gui --benchmark --version --help"
    
    # Commands
    commands="create extract list compress decompress verify"
    
    # Algorithm options
    algorithms="LZW HUFFMAN DEFLATE"
    
    case "${prev}" in
        --algo)
            COMPREPLY=( $(compgen -W "${algorithms}" -- ${cur}) )
            return 0
            ;;
        techcompressor|techcmp)
            COMPREPLY=( $(compgen -W "${opts} ${commands}" -- ${cur}) )
            return 0
            ;;
        create|c)
            COMPREPLY=( $(compgen -d -- ${cur}) )
            return 0
            ;;
        extract|x|list|l|compress|decompress|verify)
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac
    
    COMPREPLY=( $(compgen -W "${opts} ${commands}" -- ${cur}) )
    return 0
}

complete -F _techcompressor techcompressor
complete -F _techcompressor techcmp
