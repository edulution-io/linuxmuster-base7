#!/bin/sh
# /etc/profile.d/Z99-linuxmuster.sh
#
# The motd of the server, printed on every interactive login. sshd itself has
# PrintMotd off (see linuxmuster-prepare share/templates/sshd_config), so this
# is the banner an ssh session shows.
#
# thomas@linuxmuster.net
# credits to joanna
# 20260624
#
# edulution fork:
#   - every version is printed with its ~edu suffix highlighted, so a glance
#     at the banner tells which packages are edulution builds and which still
#     came from deb.linuxmuster.net,
#   - a framed note at the bottom says where the updates come from, the one
#     thing the versions alone cannot show.
#

upSeconds="$(/usr/bin/cut -d. -f1 /proc/uptime)"
secs=$((${upSeconds}%60))
mins=$((${upSeconds}/60%60))
hours=$((${upSeconds}/3600%24))
days=$((${upSeconds}/86400))
UPTIME=`printf "%d days, %02dh%02dm%02ds" "$days" "$hours" "$mins" "$secs"`
MEM=`free -m | awk 'NR==2{printf "%s/%sMB (%.2f", $3,$2,$3*100/$2 }'`
IPint=`ip a | grep glo | awk '{print $2}' | head -1 | cut -f1 -d/`
IPext=`wget -q -O - http://ipinfo.io/ip | tail`

# Colours. These are interpolated into the format string of the printf below,
# which is what turns the "\e" into an escape - exactly as the values are.
C_LBL='\e[38;5;15m'   # white, the labels
C_VAL='\e[38;5;208m'  # orange, the values
C_EDU='\e[38;5;39m'   # edulution blue (#1084c0), the ~edu suffix
C_DIM='\e[38;5;244m'  # grey, for a package that is not installed
C_DRK='\e[38;5;24m'   # dark teal, as upstream closes these lines
C_RST='\e[0m'

# The "e" of edulution is set in italics, the way Euler's number is set in
# mathematics. The codepoints meant for it, U+212F SCRIPT SMALL E and U+2147
# DOUBLE-STRUCK ITALIC SMALL E, are not an option here: DejaVu Sans Mono,
# Liberation Mono and Ubuntu Mono carry neither, so most terminals would draw
# a replacement box, and the fallback to a proportional font would shift the
# frame below. SGR 3 needs no glyph, takes no width, and a terminal that does
# not do italics simply prints an upright "e".
S_ITAL='\e[3m'
S_UPRI='\e[23m'
EDU="${S_ITAL}e${S_UPRI}dulution"

# Reads the version of an installed package, empty if it is not installed.
# Only linuxmuster-base7, -linbo7 and sophomorix-samba are guaranteed to be
# there; tools7, cli7, api7 and the LINBO GUI are separate packages, and
# querying a missing one would print a dpkg error over the banner.
pkgversion() {
    dpkg-query -W -f='${Status} ${Version}' "$1" 2>/dev/null \
        | awk '$1 == "install" && $3 == "installed" { print $4 }'
}

# The version as the banner states it, coloured: the Debian epoch is dropped
# because it carries no information for the reader, and the ~edu suffix of an
# edulution build is highlighted so a forked package stands out from an
# upstream one. An empty argument means the package is not installed.
eduversion() {
    if [ -z "$1" ] ; then
        printf '%s' "${C_DIM}not installed"
        return
    fi
    _v="${1#*:}"
    case "$_v" in
        *~edu*) printf '%s' "${C_VAL}${_v%%~edu*}${C_EDU}~edu${_v#*~edu}" ;;
        *)      printf '%s' "${C_VAL}${_v}" ;;
    esac
}

VERSIONbase7=`pkgversion linuxmuster-base7`
VERSIONlinbo7=`pkgversion linuxmuster-linbo7`
VERSIONgui7=`pkgversion edulution-linbo-gui7`
VERSIONsophomorix=`pkgversion sophomorix-samba`
VERSIONtools7=`pkgversion linuxmuster-tools7`
VERSIONapi7=`pkgversion linuxmuster-api7`
VERSIONcli7=`pkgversion linuxmuster-cli7`

# The epoch of the fork would otherwise turn "7.4.24~edu" into "1:7" here.
VERSIONlmn=`echo "${VERSIONbase7#*:}" | awk -F\. '{print $1 "." $2}'`
CODEname=`cat /etc/linuxmuster/codename`

# Where the packages come from. lmn-appliance writes the deb822 form,
# edulution-installer's playbook the one-line form, so both are searched -
# only the file names apt itself reads, so a leftover .list.save or
# .distUpgrade does not count, and only lines that are not commented out.
EDUREPO=""
for _f in /etc/apt/sources.list /etc/apt/sources.list.d/*.list \
          /etc/apt/sources.list.d/*.sources ; do
    [ -f "$_f" ] || continue
    if grep -qs '^[^#]*package\.edulution\.io' "$_f" ; then
        EDUREPO="yes"
        break
    fi
done

# Is anything on this server an edulution build at all?
EDUPKGS=""
case "$VERSIONbase7$VERSIONlinbo7$VERSIONgui7$VERSIONtools7$VERSIONapi7$VERSIONcli7$VERSIONsophomorix" in
    *~edu*) EDUPKGS="yes" ;;
esac

# The note at the bottom. BOX_W is its visible width, both borders included.
BOX_W=70

# A row of dashes. tr works on bytes, so it cannot write a multi-byte box
# character - sed can.
boxdashes() {
    printf "%${1}s" "" | sed 's/ /─/g'
}

# The single, centred line of the note. $1 is its plain text and $2 the same
# text rendered, which carries colour escapes of no visible width - so the
# centring is measured on $1.
boxline() {
    _left=$(( (BOX_W - 2 - ${#1}) / 2 ))
    [ $_left -lt 0 ] && _left=0
    _right=$(( BOX_W - 2 - _left - ${#1} ))
    [ $_right -lt 0 ] && _right=0
    printf '%s' "${C_DRK}│${C_RST}$(printf "%${_left}s" "")$2$(printf "%${_right}s" "")${C_DRK}│${C_RST}"
}

# The note below the banner: where the updates come from. Two states are
# worth telling apart - they come from edulution, or edulution packages are
# installed without the repository, and then nothing updates them any more.
# On a stock linuxmuster.net server neither is the case and the note stays
# away, together with every ~edu suffix, leaving the banner upstream has.
NOTE1=""
NOTE1C=""
if [ -n "$EDUREPO" ] ; then
    NOTE1="You are using the edulution package repository"
    NOTE1C="${C_LBL}You are using the ${C_EDU}${EDU}${C_LBL} package repository${C_RST}"
elif [ -n "$EDUPKGS" ] ; then
    NOTE1="edulution repository not configured - no updates"
    NOTE1C="${C_VAL}${EDU} repository not configured - no updates${C_RST}"
fi

EDUNOTE=""
if [ -n "$NOTE1" ] ; then
    EDUNOTE="
  ${C_DRK}╭$(boxdashes $(( BOX_W - 2 )))╮${C_RST}
  $(boxline "$NOTE1" "$NOTE1C")
  ${C_DRK}╰$(boxdashes $(( BOX_W - 2 )))╯${C_RST}"
fi

LOGO_WIDTH=46
TITLE="WELCOME TO LINUXMUSTER.NET ${VERSIONlmn} - ${CODEname}"
DATESTR=$(date +"%A, %e %B %Y, %T")
TITLE_PAD=$(( (LOGO_WIDTH - ${#TITLE}) / 2 ))
DATE_PAD=$(( (LOGO_WIDTH - ${#DATESTR}) / 2 ))
[ $TITLE_PAD -lt 0 ] && TITLE_PAD=0
[ $DATE_PAD -lt 0 ] && DATE_PAD=0
TITLE_SP=$(printf "%${TITLE_PAD}s" "")
DATE_SP=$(printf "%${DATE_PAD}s" "")

printf "
\e[38;5;15m${TITLE_SP}\e[4m${TITLE}\e[38;5;208m\e[24m
\e[38;5;15m${DATE_SP}${DATESTR}\e[38;5;208m

  ███               ███
 █████             █████    ${C_LBL} Uptime..........: ${C_VAL}${UPTIME}${C_VAL}
  ███               ███     ${C_LBL} Memory..........: ${C_VAL}${MEM}"%%\)"${C_VAL}
      ███       ███         ${C_LBL} IP Internal.....: ${C_VAL}${IPint}${C_VAL}
     █████     █████        ${C_LBL} IP External.....: ${C_VAL}${IPext}${C_VAL}
      ███       ███         ${C_DRK}
           ███              ${C_LBL} linuxmuster.net packages:${C_DRK}
          █████             ${C_LBL} -Base...........: $(eduversion "$VERSIONbase7")${C_DRK}
           ███              ${C_LBL} -Linbo..........: $(eduversion "$VERSIONlinbo7")${C_VAL}
      ███       ███         ${C_LBL} -LINBO GUI......: $(eduversion "$VERSIONgui7")${C_VAL}
     █████     █████        ${C_LBL} -Tools..........: $(eduversion "$VERSIONtools7")${C_VAL}
      ███       ███         ${C_LBL} -API............: $(eduversion "$VERSIONapi7")${C_VAL}
  ███               ███     ${C_LBL} -CLI............: $(eduversion "$VERSIONcli7")${C_VAL}
 █████             █████    ${C_LBL} -Sophomorix.....: $(eduversion "$VERSIONsophomorix")${C_VAL}
  ███               ███
${EDUNOTE}
\e[0m
"
