$TTL 300
@ IN SOA localhost. hostmaster.bd-king-r7.com. (
    2026110302 ; serial
    3600       ; refresh
    900        ; retry
    1209600    ; expire
    300        ; negative cache
)
; Local BIND test template only; Cloudflare is the intended public DNS provider.
; Add the root A record only after the real public IPv4 is confirmed.
; @ IN A REAL_ORIGIN_IPV4
www IN CNAME bd-king-r7.com.
