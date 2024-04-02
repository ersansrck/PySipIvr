



import hashlib,os,time
import secrets
class DigestAuth:
    """Attaches HTTP Digest Authentication to the given Request object."""

    @staticmethod
    def build_digest_header(sipUsername,sipPassword, method=None,urione=None,realm=None,nonce=None,algorithm=None,qop=None,opaque=None,uri=None):
        """
        :rtype: str
        """
        hash_utf8 = None
 
        if not uri:
            uri=urione
            
        if algorithm is None:
            _algorithm = "MD5"
        else: 
            _algorithm = algorithm.upper()
        # lambdas assume digest modules are imported at the top level
        if _algorithm == "MD5" or _algorithm == "MD5-SESS":

            def md5_utf8(x):
                if isinstance(x, str):
                    x = x.encode("utf-8")
                return hashlib.md5(x).hexdigest()

            hash_utf8 = md5_utf8
        elif _algorithm == "SHA":

            def sha_utf8(x):
                if isinstance(x, str):
                    x = x.encode("utf-8")
                return hashlib.sha1(x).hexdigest()

            hash_utf8 = sha_utf8
        elif _algorithm == "SHA-256":

            def sha256_utf8(x):
                if isinstance(x, str):
                    x = x.encode("utf-8")
                return hashlib.sha256(x).hexdigest()

            hash_utf8 = sha256_utf8
        elif _algorithm == "SHA-512":

            def sha512_utf8(x):
                if isinstance(x, str):
                    x = x.encode("utf-8")
                return hashlib.sha512(x).hexdigest()

            hash_utf8 = sha512_utf8

        KD = lambda s, d: hash_utf8(f"{s}:{d}")  # noqa:E731

        if hash_utf8 is None:
            return None
        
        # XXX not implemented yet
        entdig = None 
        #: path is request-uri defined in RFC 2616 which should not be empty 

        A1 = f"{sipUsername}:{realm}:{sipPassword}"
        A2 = f"{method}:{uri}"

        HA1 = hash_utf8(A1)
        HA2 = hash_utf8(A2)

        thread_nonce_count=1
        ncvalue = f"{thread_nonce_count:08x}"
        s = str(thread_nonce_count).encode("utf-8")
        s += nonce.encode("utf-8")
        s += time.ctime().encode("utf-8")
        s += os.urandom(8)

        
        cnonce = secrets.token_hex(16)
        if _algorithm == "MD5-SESS":
            HA1 = hash_utf8(f"{HA1}:{nonce}:{cnonce}")

        if not qop:
            respdig = KD(HA1, f"{nonce}:{HA2}")
        elif qop == "auth" or "auth" in qop.split(","): 
            noncebit = f"{nonce}:{ncvalue}:{cnonce}:auth:{HA2}"
            respdig = KD(HA1, noncebit)
        else:
            # XXX handle auth-int.
            return None
 

        # XXX should the partial digests be encoded too?
        base = (
            f'username="{sipUsername}", realm="{realm}", nonce="{nonce}", '
            f'uri="{uri}", response="{respdig}"'
        )
        if opaque:
            base += f', opaque="{opaque}"'
        if algorithm:
            base += f', algorithm={algorithm}'
        if entdig:
            base += f', digest="{entdig}"'
        if qop:
            base += f', qop=auth, nc={ncvalue}, cnonce="{cnonce}"'

        return f"Digest {base}" 
  
