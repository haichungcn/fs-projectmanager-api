from app import db, Excerpt


excerpts = [ 
    'First we clone it. Then we branch it. Then we add it. Then we commit it. Then we push it.',
    'Then we choose a dependency to run it.',
    'Heroku is used for production.',
    'The order, number, and datatype of our functions, along with its return, are considered the signature of the function.',
    'HTML is for structure.',
    'CSS is for styling.',
    'JS adds behavior.',
    'React was built by Facebook.',
    'Bootstrap was originally developed by Twitter.',
    'Some basic datatypes are String, Number, Array, and Object. The types of data vary from language to language.',
    'We should make sure not to add our venv to Git.',
    'We should make sure not to add our .env to Git.',
    'Eda Lovelace is a women who is widely considered to be the worlds first programmer.',
    "Python dictionaries are the same as JS objects.",
    "We should probably stick to Flexbox as much as we can.",
    "We should probably stick to Flexbox as much as we can.",
    "SQL means Structured Query Language.",
    "We can produce APIs with Flask if we want to.",
    "If we choose to return JSON from our Flask API, we can also manage back ends on mobile applications.",
    "React Native follows most of the core principles of React.",
    "Justify content center should sound familiar.",
    "React Bootstrap contains components as well as Bootstrap.",
    "We havent learned how to do push notifications yet.",
    "Hello", 
    "World"
];

for excerpt in excerpts:
    new_excerpt=Excerpt(
            body=excerpt
    )
    db.session.add(new_excerpt)
    db.session.commit()