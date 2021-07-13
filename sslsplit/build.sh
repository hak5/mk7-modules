#!/bin/bash

MODULENAME=$(basename $PWD)

check_workspace() {
    if [[ ! -d "node_modules" ]]; then
        while true; do
            read -p "[!!] The Angular workspace has not been prepared. Would you like to do it now? [Y\n] " yn
            case $yn in
                [Yy]* ) prepare_workspace; break;;
                [Nn]* ) exit 1;;
                * ) prepare_workspace; break;;
            esac
        done
    fi
}

prepare_workspace() {
    echo "[*] Preparing the Angular workspace."

    if ! command -v npm &> /dev/null; then
        echo "[!] NPM does not appear to be installed on this system. Failed to create workspace."
        return
    fi

    if ! npm install &> /dev/null; then
        echo "[!] Failed to prepare workspace. Run npm install to see why."
        return
    fi

    echo "[*] Prepared the Angular workspace successfully."
}

build_module() {
    ./node_modules/@angular/cli/bin/ng build --prod > /dev/null 2>&1
    RET=$?

    if [[ $RET -ne 0 ]]; then
        echo "[!] Angular Build Failed: Run 'ng build --prod' to figure out why."
        exit 1
    else
        echo "[*] Angular Build Succeeded"
    fi

    # Step 2: Copy the required files to the build output
    cp -r projects/$MODULENAME/src/module.svg dist/$MODULENAME/bundles/
    cp -r projects/$MODULENAME/src/module.json dist/$MODULENAME/bundles/
    cp -r projects/$MODULENAME/src/module.py dist/$MODULENAME/bundles/ > /dev/null 2>&1
    cp -r projects/$MODULENAME/src/module.php dist/$MODULENAME/bundles/ > /dev/null 2>&1
    cp -r projects/$MODULENAME/src/assets/ dist/$MODULENAME/bundles/ > /dev/null 2>&1

    # Step 3: Clean up
    rm -rf dist/$MODULENAME/bundles/*.map
    rm -rf dist/$MODULENAME/bundles/*.min*
    rm -rf bundletmp
    mv dist/$MODULENAME/bundles/ bundletmp
    rm -rf dist/$MODULENAME/*
    mv bundletmp/* dist/$MODULENAME/
    rm -rf bundletmp
}

package() {
    VERS=$(cat dist/$MODULENAME/module.json | grep "version" | awk '{split($0, a, ": "); gsub("\"", "", a[2]); gsub(",", "", a[2]); print a[2]}')
    rm -rf $MODULENAME-$VERS.tar.gz
    echo "[*] Packaging $MODULENAME (Version $VERS)"
    cd dist/
    tar -pczf $MODULENAME-$VERS.tar.gz $MODULENAME
    mv $MODULENAME-$VERS.tar.gz ../
    cd ../
}

copy_to_device() {
    echo "[*] Copying module to WiFi Pineapple via SCP"
    scp -r dist/$MODULENAME root@172.16.42.1:/pineapple/modules
}

main() {
    check_workspace
    build_module

    if [[ $1 == "package" ]]; then
        package
    elif [[ $1 == "copy" ]]; then
        copy_to_device
    fi

    echo "[*] Success!"
}

main $1