import logging
from fastapi import APIRouter, HTTPException, status

class HomeRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/", self.index, methods=["GET"])
        
    def index(self):
        try:
            return {"message": "Hello World!"}
        except HTTPException as e:
            raise e
        except Exception as e:
            logging.error(f"Erro inesperado: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor.")