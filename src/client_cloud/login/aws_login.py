from warrant import Cognito

def cognito_login(username, password, user_pool_id, client_id, region):
    try:
        u = Cognito(user_pool_id, client_id, username=username, user_pool_region=region)
        u.authenticate(password=password)

        return {
            "access_token": u.access_token,
            "id_token": u.id_token,
            "refresh_token": u.refresh_token
        }

    except Exception as e:
        print(f"❌ Errore durante il login: {e}")
        return None
