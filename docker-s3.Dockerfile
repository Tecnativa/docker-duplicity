FROM tecnativa/duplicity:docker
ENV JOB_500_WHAT='duplicity full $OPTIONS $DST' \
    JOB_500_WHEN='monthly' \
    JOB_600_WHAT='duplicity remove-older-than 3M --force $OPTIONS $DST' \
    JOB_600_WHEN='weekly' \
    OPTIONS='--file-prefix-archive archive-$(hostname)- --file-prefix-manifest manifest-$(hostname)- --file-prefix-signature signature-$(hostname)- --s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-ia --s3-use-new-style'
