from flask import Flask, redirect, request, abort, send_file, make_response
from datetime import datetime
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError, NoResultFound
from db_tables import User, Tracker, RedirectLink, TrackerRecord, TimingRecord
import geoip2.database
import time
import uuid
import traceback

app = Flask(__name__)

failed = lambda x: {'status': 'failed', 'message': x}
success = lambda x: {'status': 'success', 'message': x}

def resolve_headers(request):
    client_ip = request.headers.get("Cf-Connecting-Ip", request.remote_addr)
    if client_ip == '127.0.0.1':
        return client_ip, 'Local', 'Local', 'Local'
    with geoip2.database.Reader('GeoLite2-City.mmdb') as reader:
        response = reader.city(client_ip)
        country = response.country.names.get('zh-CN', 'Unknown')
        city = response.city.names.get('zh-CN', 'Unknown')
        isp = response.traits.network.get('isp', 'Unknown')
    return client_ip, country, city, isp

@app.route('/pixels/<int:tracker_id>.png')
def pixel_tracker(tracker_id):
    try:
        ip, country, city, isp = resolve_headers(request)
        db_session  = session_factory()
        tracker: Tracker = db_session.query(Tracker).filter(Tracker.tracker_id == tracker_id).one()
        if not tracker or tracker.tracker_type != 'pixel':
            abort(404)
        if tracker.status == 'disabled':
            return send_file("pixel.png", mimetype='image/png')
        
        record = TrackerRecord(
            tracker_id=tracker_id,
            access_time=datetime.now(),
            access_ip=ip,
            country=country,
            city=city,
            isp=isp,
            request_header=str(request.headers)
        )
        db_session.add(record)
        db_session.commit()

        if tracker.timing_enabled:
            timing_record = TimingRecord(
                record_id=record.record_id,
                last_access_time=datetime.now(),
                redirect_count=0
            )
            db_session.add(timing_record)
            db_session.commit()
            return redirect(f'/timing/1/{record.record_id}.png')
        else:
            return send_file("pixel.png", mimetype='image/png')
    except Exception as e:
        traceback.print_exc()
    finally:
        if db_session:
            db_session.close()
        
@app.route('/timing/<int:redirected_times>/<int:record_id>.png')
def timing_tracker(redirected_times, record_id):
    try:
        db_session = session_factory()
        record: TrackerRecord = db_session.query(TrackerRecord).filter(TrackerRecord.record_id == record_id).one()
        if not record:
            abort(404)
        
        timing_record = db_session.query(TimingRecord).filter(TimingRecord.record_id == record_id).one()
        timing_record.redirect_count = redirected_times
        timing_record.last_access_time = datetime.now()
        
        db_session.add(timing_record)
        db_session.commit()
        
        if(redirected_times >= 20):
            return send_file("pixel.png", mimetype='image/png')
        else:
            time.sleep(3)
            return redirect(f'/timing/{redirected_times+1}/{record_id}.png')
        
    except Exception as e:
        traceback.print_exc()
    finally:
        if db_session:
            db_session.close()

@app.route('/url/<int:tracker_id>')
def url_tracker(tracker_id):
    try:
        ip, country, city, isp = resolve_headers(request)
        db_session  = session_factory()
        tracker: Tracker = db_session.query(Tracker).filter(Tracker.tracker_id == tracker_id).one()
        if not tracker or tracker.tracker_type != 'url':
            abort(404)
        
        redirect_link: RedirectLink = \
            db_session.query(RedirectLink). \
            filter(RedirectLink.tracker_id == tracker_id).one()
        
        if tracker.status == 'disabled':
            return redirect(redirect_link.redirect_url)
        
        record = TrackerRecord(
            tracker_id=tracker_id,
            access_time=datetime.now(),
            access_ip=ip,
            country=country,
            city=city,
            isp=isp,
            request_header=str(request.headers)
        )
        db_session.add(record)
        db_session.commit()
        return redirect(redirect_link.redirect_url)
    except Exception as e:
        traceback.print_exc()
    finally:
        if db_session:
            db_session.close()

@app.post('/login')
def login():
    try:
        db_session  = session_factory()
        username = request.form.get('username')
        password = request.form.get('password')
        session_id = uuid.uuid4()
        
        user: User = db_session.query(User).\
            filter(User.username == username, User.password_hash == password).one()
    
        if not user:
            return failed("登录失败，用户名或密码错误")
        
        user.session_id = session_id
        db_session.commit()
        
        resp = make_response(success("登录成功"))
        resp.set_cookie('session_id', str(session_id))
        return resp
    
    except Exception as e:
        traceback.print_exc()
        return failed("登录失败，用户名或密码错误")
    finally:
        if db_session:
            db_session.close()
        
@app.post('/register')
def register():
    try:
        db_session = session_factory()
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User(
            username=username,
            password_hash=password,
        )
        
        db_session.add(user)
        db_session.commit()
        return success("注册成功")
    
    except Exception as e:
        traceback.print_exc()
        return failed("注册失败，用户名已存在")
    finally:
        if db_session:
            db_session.close()
    
@app.post('/list_trackers')
def list_trackers():
    try:
        db_session = session_factory()
        session_id = request.cookies.get('session_id')
        
        trackers = db_session.query(Tracker).\
            join(User).\
            filter(User.session_id == session_id).all()\
        
        trackers = list(map(lambda x: x.__dict__, trackers))
        list(map(lambda x: x.pop('_sa_instance_state'), trackers))
        return {'status': 'success', 'message': "获取成功", 'trackers': trackers}
    
    except Exception as e:
        traceback.print_exc()
        return failed("失败")
    finally:
        if db_session:
            db_session.close()
    
@app.post('/add_tracker')
def add_tracker():
    try:
        db_session = session_factory()
        session_id = request.cookies.get('session_id')
        user = db_session.query(User).filter(User.session_id == session_id).one()
        
        new_tracker = Tracker(
            alias="Your Tracker Name",
            description="Your Tracker Description",
            user_id=user.user_id,
            tracker_type="pixel",
            timing_enabled=False,
            status="disabled"
        )
        
        db_session.add(new_tracker)
        db_session.commit()
        return {'status': 'success', 'message': "创建成功", \
            'id': new_tracker.tracker_id}
    
    except Exception as e:
        traceback.print_exc()
        return failed("失败")
    finally:
        if db_session:
            db_session.close()

@app.post('/tracker_info/<int:tracker_id>')
def tracker_info(tracker_id):
    try:
        db_session = session_factory()
        session_id = request.cookies.get('session_id')
        user = db_session.query(User, Tracker, RedirectLink).\
            join(Tracker, User.user_id == Tracker.user_id).\
            join(RedirectLink, 
                 Tracker.tracker_id == RedirectLink.tracker_id,
                 isouter=True).\
            filter(User.session_id == session_id, 
                   Tracker.tracker_id == tracker_id).one()
        if not user:
            return failed("失败")

        # print(user.Tracker.__dict__)
        info = user.Tracker.__dict__
        info.pop('_sa_instance_state')
        info['redirect_url'] = "" if user.RedirectLink is None else user.RedirectLink.redirect_url
        return {'status': 'success', 'message': "获取成功", 'info': info}
    except Exception as e:
        traceback.print_exc()
        return failed("失败")
    finally:
        if db_session:
            db_session.close()

@app.post('/tracker_update/<int:tracker_id>')
def tracker_update(tracker_id):
    try:
        db_session = session_factory()
        session_id = request.cookies.get('session_id')
        alias = request.form.get('alias')
        description = request.form.get('description')
        tracker_type = request.form.get('tracker_type')
        timing_enabled = True if request.form.get('timing_enabled') == 'true' else False
        status = request.form.get('status')
        tracker = db_session.query(Tracker).\
            join(User).\
            filter(User.session_id == session_id, 
                   Tracker.tracker_id == tracker_id).one()
        
        tracker.alias = alias if alias else tracker.alias
        tracker.description = description if description else tracker.description
        tracker.tracker_type = tracker_type if tracker_type else tracker.tracker_type
        tracker.timing_enabled = timing_enabled if request.form.get('timing_enabled') else tracker.timing_enabled
        tracker.status = status if status else tracker.status
        db_session.add(tracker)
        db_session.commit()
        return success("更新成功")
    except Exception as e:
        traceback.print_exc()
        return failed("失败")
    finally:
        if db_session:
            db_session.close()

@app.post('/tracker_records/<int:tracker_id>')
def tracker_records(tracker_id):
    try:
        db_session = session_factory()
        session_id = request.cookies.get('session_id')
        records = db_session.query(TrackerRecord, TimingRecord).\
            join(Tracker).\
            join(User).\
            join(TimingRecord, 
                 TimingRecord.record_id == TrackerRecord.record_id,
                 isouter=True).\
            filter(User.session_id == session_id,
                   Tracker.tracker_id == tracker_id).all()        
        # records = list(map(lambda x: x.TrackerRecord.__dict__, records))
        # list(map(lambda x: x.pop('_sa_instance_state'), records))
        results = []
        for record in records:
            rec_dict = record.TrackerRecord.__dict__
            rec_dict.pop('_sa_instance_state')
            if record.TimingRecord is None:
                rec_dict['last_access_time'] = -1
                rec_dict['redirect_count'] = -1
                rec_dict['read_time'] = -1
            else:
                rec_dict['last_access_time'] = record.TimingRecord.last_access_time
                rec_dict['redirect_count'] = record.TimingRecord.redirect_count
                read_time = record.TimingRecord.last_access_time - record.TrackerRecord.access_time
                rec_dict['read_time'] = read_time.seconds + read_time.microseconds / 1000000
            results.append(rec_dict)
        return {'status': 'success', 'message': "获取成功", 'records': results}
    except Exception as e:
        traceback.print_exc()
        return failed("失败")
    finally:
        if db_session:
            db_session.close()

# 启动应用程序
if __name__ == '__main__':
    from sqlalchemy import create_engine
    CONNSTR = f'postgresql://postgres:daimeng.233@127.0.0.1/GhostKiller'
    engine = create_engine(CONNSTR)
    session_factory = sessionmaker(bind=engine)
    app.run()
