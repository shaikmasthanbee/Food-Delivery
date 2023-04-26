from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(userid,seconds):
    s=Serializer('67@hjyjhk',seconds)
    return s.dumps({'admin':userid}).decode('utf-8')