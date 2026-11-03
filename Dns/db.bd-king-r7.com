$TTL 300
@ IN SOA localhost. hostmaster.bd-king-r7.com. (
    2026110301 ; serial
    3600       ; refresh
    900        ; retry
    1209600    ; expire
    300        ; negative cache
)
; Local BIND template only. Replace origin placeholder before use.
@   IN A       REPLACE_WITH_REAL_ORIGIN_IPV4
www IN CNAME   bd-king-r7.com.
