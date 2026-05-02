# fastfetch (must run before p10k instant prompt)
if [[ -o interactive ]] && [ -f /usr/bin/fastfetch ] && [[ -z "$NOFASTFETCH" ]]; then
    fastfetch
fi

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH

# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="powerlevel10k/powerlevel10k"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to enable command auto-correction.
ENABLE_CORRECTION="true"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)

source $ZSH/oh-my-zsh.sh

#######################################################
# EXPORTS
#######################################################

# XDG directories
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_STATE_HOME="$HOME/.local/state"
export XDG_CACHE_HOME="$HOME/.cache"

# History
export HISTSIZE=10000
export SAVEHIST=10000
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_IGNORE_SPACE
setopt APPEND_HISTORY
setopt SHARE_HISTORY

# Editor
export EDITOR=mousepad
export VISUAL=mousepad

# Colors
export CLICOLOR=1

# Color for manpages in less
export LESS_TERMCAP_mb=$'\E[01;31m'
export LESS_TERMCAP_md=$'\E[01;31m'
export LESS_TERMCAP_me=$'\E[0m'
export LESS_TERMCAP_se=$'\E[0m'
export LESS_TERMCAP_so=$'\E[01;44;33m'
export LESS_TERMCAP_ue=$'\E[0m'
export LESS_TERMCAP_us=$'\E[01;32m'

export LINUXTOOLBOXDIR="$HOME/linuxtoolbox"

# PATH
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/var/lib/flatpak/exports/bin:$HOME/.local/share/flatpak/exports/bin:$PATH"

#######################################################
# GENERAL ALIASES
#######################################################

alias ebrc='$EDITOR ~/.zshrc'
alias da='date "+%Y-%m-%d %A %T %Z"'
alias cp='cp -i'
alias mv='mv -i'
alias rm='rm -i'
alias trash='trash -v'
alias mkdir='mkdir -p'
alias ps='ps auxf'
alias ping='ping -c 10'
alias less='less -R'
alias cls='clear'
alias multitail='multitail --no-repeat -c'
alias vi='nvim'
alias vim='nvim'
alias svi='sudo vi'
alias vis='nvim "+set si"'
# yayf removed — yay is Arch-only (AUR helper)

# Change directory aliases
alias home='cd ~'
alias cd..='cd ..'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias bd='cd "$OLDPWD"'

# Remove a directory and all files
alias rmd='/bin/rm --recursive --force --verbose'

#######################################################
# eza (ls replacement)
#######################################################
if command -v eza >/dev/null; then
    alias ls='eza --group-directories-first --icons'
    alias ll='eza -l --all --group-directories-first --icons'
    alias la='eza --all --group-directories-first --icons'
    alias lf='eza -l --only-files --icons'
    alias ld='eza -l --only-dirs --icons'
    alias lt='eza -l --all --sort=modified --icons'
    alias lk='eza -l --all --sort=size --icons'
    alias lh='eza -ld .* --group-directories-first --icons 2>/dev/null'
    alias lt2='eza -T --level=2 --icons'
    alias lt3='eza -T --level=3 --icons'
fi

# Search
alias h="history | grep"
alias p="ps aux | grep"
alias topcpu="/bin/ps -eo pcpu,pid,user,args | sort -k 1 -r | head -10"
alias f="find . | grep"
alias countfiles="for t in files links directories; do echo \$(find . -type \${t:0:1} | wc -l) \$t; done 2>/dev/null"
alias checkcommand="type -t"

# Network
alias openports='netstat -nape --inet'
alias rebootsafe='sudo shutdown -r now'
alias rebootforce='sudo shutdown -r -n now'

# Disk
alias diskspace="du -S | sort -n -r | more"
alias folders='du -h --max-depth=1'
alias folderssort='find . -maxdepth 1 -type d -print0 | xargs -0 du -sk | sort -rn'
alias mountedinfo='df -hT'

# Logs
alias logs="sudo find /var/log -type f -exec file {} \; | grep 'text' | cut -d' ' -f1 | sed -e's/:$//g' | grep -v '[0-9]$' | xargs tail -f"

alias sha1='openssl sha1'
alias kssh="kitty +kitten ssh"
alias matrix="unimatrix -s 95"
alias rg='rg --smart-case'
alias ufwlog='journalctl -k --grep="UFW" -f'
alias cx='claude --allowedTools Read Glob Grep WebFetch WebSearch Agent'
alias nb=newsboat
# updateffx removed — Firefox profile path is machine-specific; set manually after first launch
alias runclam='~/.local/bin/runclam'

#######################################################
# FUNCTIONS
#######################################################

# Extract archives
extract() {
    for archive in "$@"; do
        if [ -f "$archive" ]; then
            case $archive in
                *.tar.bz2) tar xvjf $archive ;;
                *.tar.gz)  tar xvzf $archive ;;
                *.bz2)     bunzip2 $archive ;;
                *.rar)     unrar x $archive ;;
                *.gz)      gunzip $archive ;;
                *.tar)     tar xvf $archive ;;
                *.tbz2)    tar xvjf $archive ;;
                *.tgz)     tar xvzf $archive ;;
                *.zip)     unzip $archive ;;
                *.Z)       uncompress $archive ;;
                *.7z)      7z x $archive ;;
                *)         echo "don't know how to extract '$archive'..." ;;
            esac
        else
            echo "'$archive' is not a valid file!"
        fi
    done
}

# Create and cd into directory
mkdirg() {
    mkdir -p "$1"
    cd "$1"
}

# Go up N directories
up() {
    local d=""
    limit=$1
    for ((i = 1; i <= limit; i++)); do
        d=$d/..
    done
    d=$(echo $d | sed 's/^\///')
    if [ -z "$d" ]; then
        d=..
    fi
    cd $d
}

# IP address lookup
alias whatismyip="whatsmyip"
whatsmyip() {
    if command -v ip &>/dev/null; then
        echo -n "Internal IP: "
        ip addr show wlan0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
    else
        echo -n "Internal IP: "
        ifconfig wlan0 | grep "inet " | awk '{print $2}'
    fi
    echo -n "External IP: "
    curl -4 ifconfig.me
}

# Trim whitespace
trim() {
    local var=$*
    var="${var#"${var%%[![:space:]]*}"}"
    var="${var%"${var##*[![:space:]]}"}"
    echo -n "$var"
}

#######################################################
# thefuck
#######################################################
fk() {
    TF_PYTHONIOENCODING=$PYTHONIOENCODING
    export TF_SHELL=zsh
    export TF_ALIAS=fk
    export TF_SHELL_ALIASES=$(alias)
    export TF_HISTORY=$(fc -ln -10)
    export PYTHONIOENCODING=utf-8
    TF_CMD=$(thefuck THEFUCK_ARGUMENT_PLACEHOLDER "$@") && eval "$TF_CMD"
    unset TF_HISTORY
    export PYTHONIOENCODING=$TF_PYTHONIOENCODING
    history -s $TF_CMD
}

#######################################################
# yazi shell wrapper
#######################################################
function y() {
    local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
    yazi "$@" --cwd-file="$tmp"
    if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
        builtin cd -- "$cwd"
    fi
    rm -f -- "$tmp"
}

#######################################################
# LocalSend UFW helpers
#######################################################
localon() {
    sudo ufw allow from 192.168.1.0/24 to any port 53317 proto tcp
    sudo ufw allow from 192.168.1.0/24 to any port 53317 proto udp
    sudo ufw allow from 192.168.3.0/24 to any port 53317 proto tcp
    sudo ufw allow from 192.168.3.0/24 to any port 53317 proto udp
    sudo ufw status numbered
}

localoff() {
    sudo ufw delete allow from 192.168.1.0/24 to any port 53317 proto tcp || true
    sudo ufw delete allow from 192.168.1.0/24 to any port 53317 proto udp || true
    sudo ufw delete allow from 192.168.3.0/24 to any port 53317 proto tcp || true
    sudo ufw delete allow from 192.168.3.0/24 to any port 53317 proto udp || true
    sudo ufw status numbered
}

mineon() {
    sudo ufw allow in on wlan0 from 192.168.3.0/24 to any
    sudo ufw status numbered
}

mineoff() {
    sudo ufw delete allow in on wlan0 from 192.168.3.0/24 to any || true
    sudo ufw status numbered
}

#######################################################
# Tool integrations
#######################################################

# zoxide
eval "$(zoxide init zsh)"
bindkey '^f' undefined-key
# Ctrl+f to trigger zi (zoxide interactive)
function _zoxide_zi_widget() {
    zi
    zle reset-prompt
}
zle -N _zoxide_zi_widget
bindkey '^f' _zoxide_zi_widget

# fzf
source <(fzf --zsh)
export FZF_DEFAULT_OPTS="--preview='bat --color=always {}' --preview-window=right:60%"

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
