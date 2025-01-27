from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text 
from db import get_db
from pandas import DataFrame 
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.execute(text("SELECT * FROM employees where user_id = :user_id"),{'user_id':user_id})
    user = user.fetchone()
    skill_ids = db.execute(text("SELECT * FROM employee_skill where employee_id = :emp_id"),{'emp_id':user.id})
    names = []
    for skill in skill_ids:
        names.append(db.execute(text("SELECT name from skills where id = :skill_id"),{'skill_id':skill.skill_id}).fetchone().name)
    if user is None:
        return {"error": "User not found"}
    ids = []
    for name in names:
        #name = name.strip()
        value = all_jobs(name,db)
        #print("Length from database",len(name),value)
        ids.append(value)
    
    return {'skills':ids}

@app.get("/jobs/{title}/")
def all_jobs(title: str, db: Session = Depends(get_db)):
    active_jobs = db.execute(text("SELECT title, description FROM job_posts"))
    if active_jobs is None:
        return {'error': "No active jobs found"}
    jobs_data = active_jobs.fetchall()
    if not jobs_data:
        return {'error': "No active jobs found"}
    df = DataFrame(jobs_data)
    if df.empty:
        return {'error': "Job data is empty"}
    df['title'] = df['title'].str.strip().str.lower()
    df['description'] = df['description'].str.strip().str.lower()
    cv = CountVectorizer(stop_words='english')
    vector = cv.fit_transform(df['description']).toarray()
    similarity = cosine_similarity(vector)
    recommendations = recommend(title.lower(), df, similarity)
    return {'active_jobs': recommendations}

def recommend(title:str,df:DataFrame,similarity):
    try:
        #index = df[df['title'].str.contains() == title.lower()].index[0]
        index = df[df['title'].str.contains(title.lower(),case=False)].index[0]
        distances = sorted(list(enumerate(similarity[index])),reverse=True,key = lambda x: x[1])
        jobs = []
        for i in distances[1:20]: 
            #jobs.append(df.iloc[i[0]]['title'])
            jobs.append(i[0]) 
        return jobs 
    except:
        return {'message':"Not Found"}