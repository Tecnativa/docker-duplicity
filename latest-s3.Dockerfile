FROM index.docker.io/tecnativa/duplicity
ENV JOB_500_WHAT='dup full $SRC $DST' \
    JOB_500_WHEN='weekly' \
    OPTIONS_EXTRA='--full-if-older-than 1W --file-prefix-archive archive-$(hostname)- --file-prefix-manifest manifest-$(hostname)- --file-prefix-signature signature-$(hostname)- --s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-new-style'
