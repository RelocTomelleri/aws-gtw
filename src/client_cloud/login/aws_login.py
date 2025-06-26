from pycognito import Cognito
from botocore.exceptions import ClientError

def cognito_login(username, password, user_pool_id, client_id, region):
    user = Cognito(user_pool_id, client_id, username=username, user_pool_region=region)
    try:
        user.authenticate(password)
        return {
            "access_token": user.access_token,
            "id_token": user.id_token,
            "refresh_token": user.refresh_token,
        }
    except ClientError as e:
        print(f"❌ Errore durante il login: {e.response['Error']['Message']}")
        return None
