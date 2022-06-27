import datetime
import hashlib
import json
from flask import Flask, jsonify

''' 돼지 코인 클래스 구현'''

class Doegecoin:

    # 돼지 코인 생성자, 빈체인 리스트, 빈트랜잭션 리스트 생성
    def __init__(self):
        self.chain = []                             # 체인
        self.current_transaction = []               # 트랜잭션

        # genesis block zerobase tx
        self.new_transaction('0', 'miner', float(10000))   

        # genesis block, 초기 nonce 값 1, 이전블록해쉬 '0'
        self.new_block(previous_block_hash = '0', merkleroot = self.get_merkleroot(), bits = self.get_bits(), nonce = 1)

    # 블록 생성 
    # 버전, 이전블록해쉬, 머클루트해쉬, 블록생성시간, 난이도, 넌스, 트랜잭션으로 구성
    def new_block(self, previous_block_hash, merkleroot, bits, nonce):
        
        # 블록 생성
        block = {
            'version' : '1.0',
            'previous_block_hash' : previous_block_hash,
            'merkleroot' : merkleroot,
            'timestamp': str(datetime.datetime.now()),
            'bits' : bits,
            'nonce' : nonce,
            'transactions' : self.current_transaction
        }

        # 트랜잭션 초기화
        self.current_transaction = []
        
        # 블록생성
        self.chain.append(block)
        return block

    # 트랜잭션 생성
    # 보내는이 주소, 받는이 주소, 보내는 총량을 인자로 받음
    def new_transaction(self, from_address, to_address, amount):
        self.current_transaction.append(
            {
                'from_address' : from_address,
                'to_address' : to_address,
                'amount' : amount
            }
        )
    
    # self.current_transaction 을 이용해 머클루트 해쉬값 도출
    def get_merkleroot(self):
        tmp = json.dumps(self.current_transaction, sort_keys = True).encode()
        return hashlib.sha256(tmp).hexdigest()

    def get_bits(self):
        # 체인의 길이가 3 늘어날 때마다 채굴난이도 증가
        return (len(self.chain) // 3) + 1
        

    # 이전 블록의 구성요소들을 불러옴
    def get_previous_block(self):
        return self.chain[-1]
    
    # nonce 계산
    # 버전, 이전블록해쉬, 머클루트, 생성시간, 생성난이도 를 받은뒤 nonce 를 대입하여 찾음
    # proof of work
    def get_nonce(self,_version, _previous_block_hash, _merkleroot, _timestamp, _bits):
        nonce = 1
        check = False

        # 헤더 6개 값의 sha256 값중 bits의 개수만큼 0 으로 시작하는 nonce 탐색 proof of work
        while check is False:
            header5 = _version + _previous_block_hash + _merkleroot + _timestamp + str(_bits) + str(nonce)
            hash_operation = hashlib.sha256(str(header5).encode()).hexdigest()

            bitszero = ''
            for i in range(_bits):
                bitszero += '0'

            if hash_operation.startswith(bitszero):
                check = True
            else:
                nonce += 1
        return nonce

    # 블록1개의 해쉬값, 이전블록해쉬값을 구하기 위한 함수
    def get_block_hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()



''' 실행 파트 '''

# Flask 이용하여 localhost 로 돼지코인 채굴 및 체인연결 실행
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
doegecoin = Doegecoin()


# http://localhost:5000/mine
# 채굴하여 nonce 값을 찾아 블록을 이어줌
@app.route('/mine', methods = ['GET'])
def mine():
    # 이전 블록 데이터 호출
    previous_block = doegecoin.get_previous_block()

    # get_nonce 함수를 호출하기 위해 이전블록 데이터 저장
    _version = previous_block['version']
    _previous_block_hash = previous_block['previous_block_hash']
    _merkleroot = previous_block['merkleroot']
    _timestamp = previous_block['timestamp']
    _bits = previous_block['bits']

    # zerobase tx
    # 처음에 10000 돼지코인 지급 후 2 의 (bits - 1) 승 만큼 반감
    bits = doegecoin.get_bits()
    amount = 10000/ (2 ** (bits - 1))
    doegecoin.new_transaction('0', 'miner', amount)

    # 새로운 블록생성을 위한 데이터 생성
    previous_block_hash = doegecoin.get_block_hash(previous_block)
    merkleroot = doegecoin.get_merkleroot()
    nonce = doegecoin.get_nonce(_version, _previous_block_hash, _merkleroot, _timestamp, _bits)

    # 새로운 블록 생성
    block = doegecoin.new_block(previous_block_hash, merkleroot, bits, nonce)

    # 채굴 완료, 현재 블록 데이터 출력
    responses = {
        **block
    }
    return jsonify(responses), 200

# http://localhost:5000/chain
# 전체 체인을 리턴해줌, 제네시스 블록부터 시작
@app.route('/chain', methods = ['GET'])
def chain():
    response = {
        'chain': doegecoin.chain
    }
    return jsonify(response), 200

# http://localhost:5000/newtx
# 트랜잭션 실행 A 가 B 에게 1000 돼지코인 송금
@app.route('/newtx', methods = ['GET'])
def tx():

    # 트랜잭션 실행
    doegecoin.new_transaction('A', 'B', 1000)

    response = {
        'from_address' : 'A',
        'to_address' : 'B',
        'amount' : 1000
    }
    return jsonify(response), 200

# 어플리케이션 실행 python3 doegecoin.py
app.run(host = '0.0.0.0', port = 5000)



'''
* read me
* python3 doegecoin.py   로 실행
* http://localhost:5000/mine    채굴 url
* http://localhost:5000/chain   전체 노드 url
* http://localhost:5000/newtx   transaction 0번
'''