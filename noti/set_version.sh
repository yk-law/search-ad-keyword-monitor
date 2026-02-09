#!/bin/bash

if [ "x$YKOS_HOME" = "x" ]; then
	echo "ERROR: YKOS_HOME is not defined. please run 'source .env' first."
	exit 1
fi

source $YKOS_HOME/scripts/sed_inplace.sh

NOTI_VERSION=`cat ${YKOS_HOME}/apps/common/version/gen_version`

cp -rp ${YKOS_HOME}/apps/noti/version.py.in ${YKOS_HOME}/apps/noti/version.py

sed_inplace 's%'"__@YKOS_NOTI_VERSION__"'%'"${NOTI_VERSION}"'%g' ${YKOS_HOME}/apps/noti/version.py
