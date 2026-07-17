from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='QUANTAURA-Core API', version='0.3')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)


@app.get('/health')
def health():
    return {'status': 'healthy'}


@app.get('/system/status')
def status():
    return {
        'status': 'operational',
        'version': '0.3',
        'platform': 'QUANTAURA-Core'
    }


@app.get('/system/info')
def info():
    return {
        'name': 'QUANTAURA-Core',
        'description': 'Unified research operating system for simulations, mathematical models, and quantitative tooling.'
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
