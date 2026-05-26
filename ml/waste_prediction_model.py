import pandas as pd

from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier

from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import (

    accuracy_score,
    classification_report
)

data = pd.DataFrame({

    "Category": [

        "Dairy",
        "Protein",
        "Vegetable",
        "Fruit",
        "Dairy",
        "Protein",
        "Vegetable",
        "Fruit",
        "Grains",
        "Protein"
    ],

    "Days_Left": [

        1,
        2,
        7,
        5,
        1,
        3,
        6,
        2,
        10,
        1
    ],

    "Quantity": [

        1,
        2,
        5,
        3,
        1,
        2,
        4,
        1,
        6,
        1
    ],

    "Waste_Risk": [

        "High",
        "High",
        "Low",
        "Medium",
        "High",
        "Medium",
        "Low",
        "Medium",
        "Low",
        "High"
    ]
})

encoder = LabelEncoder()

data["Category"] = encoder.fit_transform(

    data["Category"]
)

risk_encoder = LabelEncoder()

data["Waste_Risk"] = risk_encoder.fit_transform(

    data["Waste_Risk"]
)

X = data[[

    "Category",
    "Days_Left",
    "Quantity"
]]

y = data["Waste_Risk"]

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.2,

    random_state=42
)

model = RandomForestClassifier(

    n_estimators=100,

    random_state=42
)

model.fit(

    X_train,
    y_train
)

predictions = model.predict(
    X_test
)

accuracy = accuracy_score(

    y_test,
    predictions
)

print(
    "Waste Prediction Model Accuracy:",
    accuracy
)

print(

    classification_report(
        y_test,
        predictions
    )
)