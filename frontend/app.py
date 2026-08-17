import streamlit as st
import requests
import pandas as pd
import json
import io

# Placeholder for the backend API URL - USER MUST UPDATE THIS
# This should be the URL of your deployed Flask API (port 7860) from GitHub Codespaces
# Example: "https://organic-space-abcd1234-7860.app.github.dev"
MODEL_ROOT_URL = "http://backend:7860"

if MODEL_ROOT_URL == "_____":
    st.error("Please update the `MODEL_ROOT_URL` variable with your GitHub Codespace forwarded URL for the backend API (port 7860).")
    st.stop()

model_predict_url = f"{MODEL_ROOT_URL}/v1/predict"
model_batch_predict_url = f"{MODEL_ROOT_URL}/v1/predictbatch"

st.set_page_config(page_title="SuperKart Sales Predictor", layout="wide")

st.title("🛒 SuperKart Sales Forecasting Frontend")
st.markdown("Use this application to predict `Product_Store_Sales_Total` based on product and store attributes.")

st.sidebar.header("Prediction Type")
prediction_mode = st.sidebar.radio("Choose a prediction mode:", ("Single Prediction", "Batch Prediction"))

# --- Single Prediction ---
if prediction_mode == "Single Prediction":
    st.header("Single Product Sales Prediction")
    st.write("Enter the details of a single product and store to predict its sales.")

    # Input fields for features - based on original features required by preprocess_single_input
    col1, col2 = st.columns(2)

    with col1:
        product_weight = st.number_input("Product Weight", min_value=0.0, max_value=100.0, value=12.66, step=0.01)
        product_allocated_area = st.number_input("Product Allocated Area", min_value=0.0, max_value=1.0, value=0.027, step=0.001)
        product_mrp = st.number_input("Product MRP", min_value=0.0, max_value=1000.0, value=117.08, step=0.01)
        store_establishment_year = st.number_input("Store Establishment Year", min_value=1900, max_value=2026, value=2009, step=1)
        store_id = st.selectbox("Store ID", ['OUT004', 'OUT001', 'OUT003', 'OUT002'])

    with col2:
        product_sugar_content = st.selectbox("Product Sugar Content", ['Low Sugar', 'Regular', 'No Sugar'])
        product_type = st.selectbox("Product Type", ['Fruits and Vegetables', 'Snack Foods', 'Frozen Foods', 'Dairy', 'Household', 'Baking Goods', 'Canned', 'Health and Hygiene', 'Meat', 'Soft Drinks', 'Breads', 'Hard Drinks', 'Others', 'Starchy Foods', 'Breakfast', 'Seafood'])
        store_size = st.selectbox("Store Size", ['Medium', 'High', 'Small'])
        store_location_city_type = st.selectbox("Store Location City Type", ['Tier 2', 'Tier 1', 'Tier 3'])
        store_type = st.selectbox("Store Type", ['Supermarket Type2', 'Supermarket Type1', 'Departmental Store', 'Food Mart'])


    predict_button = st.button("Predict Sales")

    if predict_button:
        # Create payload for the API request
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar_content,
            "Product_Allocated_Area": product_allocated_area,
            "Product_Type": product_type,
            "Product_MRP": product_mrp,
            "Store_Id": store_id,
            "Store_Establishment_Year": store_establishment_year,
            "Store_Size": store_size,
            "Store_Location_City_Type": store_location_city_type,
            "Store_Type": store_type
        }

        try:
            response = requests.post(model_predict_url, json=payload)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            prediction_result = response.json()

            if "prediction" in prediction_result:
                st.success(f"Predicted `Product_Store_Sales_Total`: **{prediction_result['prediction']:.2f}**")
            elif "error" in prediction_result:
                st.error(f"Error from API: {prediction_result['error']}")
            else:
                st.error("Unexpected response from API.")
                st.json(prediction_result)

        except requests.exceptions.ConnectionError:
            st.error(f"Connection Error: Could not connect to the API at {model_predict_url}. Please ensure your Codespace is running and the URL is correct.")
        except requests.exceptions.Timeout:
            st.error("Timeout Error: The request took too long to respond.")
        except requests.exceptions.RequestException as e:
            st.error(f"An unexpected error occurred: {e}")
            if hasattr(response, 'text'):
                st.error(f"API Response: {response.text}")

# --- Batch Prediction ---
elif prediction_mode == "Batch Prediction":
    st.header("Batch Product Sales Prediction")
    st.write("Upload a CSV file containing product and store data to get batch predictions.")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        try:
            batch_df = pd.read_csv(uploaded_file)
            st.write("Uploaded Data Preview:")
            st.dataframe(batch_df.head())

            # Check if all required columns are present in the uploaded CSV
            required_cols_for_batch = [
                "Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area",
                "Product_Type", "Product_MRP", "Store_Id", "Store_Establishment_Year",
                "Store_Size", "Store_Location_City_Type", "Store_Type"
            ]
            missing_cols = [col for col in required_cols_for_batch if col not in batch_df.columns]

            if missing_cols:
                st.error(f"Missing required columns in CSV: {', '.join(missing_cols)}. Please ensure your CSV has all necessary input features.")
            else:
                batch_predict_button = st.button("Get Batch Predictions")

                if batch_predict_button:
                    # Prepare batch input for API request
                    # The API expects a file, so we convert the dataframe to CSV bytes
                    files = {
                        'file': (uploaded_file.name, batch_df.to_csv(index=False).encode('utf-8'), 'text/csv')
                    }

                    try:
                        with st.spinner("Getting predictions..."):
                            response = requests.post(model_batch_predict_url, files=files)
                            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                            batch_predictions_result = response.json()

                        if "predictions" in batch_predictions_result:
                            predictions_df = pd.DataFrame(batch_predictions_result['predictions'], columns=['Predicted_Sales_Total'])
                            results_df = pd.concat([batch_df, predictions_df], axis=1)
                            st.subheader("Batch Prediction Results:")
                            st.dataframe(results_df)

                            csv_output = results_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="Download Predictions as CSV",
                                data=csv_output,
                                file_name="superkart_batch_predictions.csv",
                                mime="text/csv",
                            )
                        elif "error" in batch_predictions_result:
                            st.error(f"Error from API: {batch_predictions_result['error']}")
                        else:
                            st.error("Unexpected response from API.")
                            st.json(batch_predictions_result)

                    except requests.exceptions.ConnectionError:
                        st.error(f"Connection Error: Could not connect to the API at {model_batch_predict_url}. Please ensure your Codespace is running and the URL is correct.")
                    except requests.exceptions.Timeout:
                        st.error("Timeout Error: The request took too long to respond.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"An unexpected error occurred: {e}")
                        if hasattr(response, 'text'):
                            st.error(f"API Response: {response.text}")

        except Exception as e:
            st.error(f"Error processing the uploaded file: {e}")
