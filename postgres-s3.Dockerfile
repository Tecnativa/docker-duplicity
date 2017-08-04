FROM tecnativa/duplicity:postgres
ENV JOB_500_WHAT='dup full $SRC $DST' \
    JOB_500_WHEN='monthly' \
    JOB_600_WHAT='dup remove-older-than 3M --force $DST' \
    JOB_600_WHEN='weekly' \
    OPTIONS_EXTRA='--full-if-older-than 1M --file-prefix-archive archive-$(hostname)- --file-prefix-manifest manifest-$(hostname)- --file-prefix-signature signature-$(hostname)- --s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-ia --s3-use-new-style'
