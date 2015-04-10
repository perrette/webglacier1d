# download all greenland data from the cluster
# provide a file name containing a list of files as first argument

# look data directory in config.py file
echo "Read data directory in config.py"
datadir=`python -c 'import config; print config.datadir'`
echo "Download data in $datadir?"
echo "y/[n]?"
read ans
if [[ "$ans" != 'y' ]] ; then
    echo "you can set the path in config.py"
    exit
fi
if [[ "$1" == "" ]]; then
    echo "No data file specified. Download all data?"
    echo "y/[n]?"
    read ans
    if [ $ans != 'y' ] ; then
        echo "Please write required data names to a file and pass the file name to this script as first argument (--files-from parameter for rsync)"
        exit
    fi
    FILES=""
else
    FILES="--files-from=$1"
fi

# create download directory if does not already exist
cmd="mkdir $datadir -p"
echo $cmd
`$cmd`

# download data
rsync -ar --progress $FILES $CLU:/iplex/01/megarun/perrette/data/greenland/ $datadir
# cmd="rsync -ar --progress $FILES $CLU:/iplex/01/megarun/perrette/data/greenland/ $datadir"
# echo $cmd
# `$cmd`
#rsync -ar --progress --files-from=/home/perrette/GreenlandOutletGlaciers/scripts/dataanalysis/bokehapp/requiredfiles.txt cluster.pik-potsdam.de:/iplex/01/megarun/perrette/data/greenland/ /home/perrette/data/greenland
