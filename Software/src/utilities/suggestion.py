from groq import Groq


class Suggestion():
    def __init__(self, api):
        self.normal_npkw = ["30-60", "20-40", "100-300", "40-80"]
        self.client = Groq(
            api_key= f"{api}",
        )

    def get_field_suggetion(self, npkw_values):

        messages = [
            {
                "role": "user",
                "content": f"""


                The NPK values for the specific part of the field are as follows:
                - Nitrogen: {npkw_values[0]} mg/kg
                - Phosphorus: {npkw_values[1]} mg/kg
                - Potassium: {npkw_values[2]} mg/kg
                The current water level for this part of the field is  {npkw_values[3]}%.

                The normal range for the npkw for a field cultivating potato-plant is 
                - Nitrogen: {self.normal_npkw[0]} mg/kg
                - Phosphorus: {self.normal_npkw[1]} mg/kg
                - Potassium: {self.normal_npkw[2]} mg/kg
                - Water : {self.normal_npkw[3]} %
                
                Please provide an analysis and suggestion of each value i am giving you the format:
                1. First tell me the value for each for the part of that field i have given you
                2. What should the ideal NPK and water values be for optimal crop growth in this field?
                3. In the analysis section tell me about each value of the field and compare to the normal value and tell if increase and dicrease tell me the consiquesce for each value for the potato plant like disease for hte value i gave given for the part of the field. Tell me each for each section
                4. Based on this analysis, suggest any fertilizers, soil amendments, or treatments that should be applied to improve the part of the field conditions.

                Finally listen add no '*' characte for section or list as it seem meesy instead of this ,in the response use normal numbering or for each seciotn an new line for subsection.
                and make the response in very big at least 1000 words and use easier and simple word
                
                """,
            }
        ]
        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",
        )

        data = chat_completion.choices[0].message.content
        data = data.replace('*', '')
        data = data.replace('**', '')
        return data



    def get_disease_suggestion(self,npkw_values, disease_name):
        messages = [
            {
                "role": "user",
                "content": f"""
            The following data has been collected for analyzing a specific potato plant disease in a part of the field. The NPK values (Nitrogen, Phosphorus, Potassium) have been measured from the root zone of the diseased potato plants in the affected area. These values are being provided for detailed analysis to understand if there is any relationship between the nutrient levels and the occurrence of the disease. 

            Here are the details for the affected part of the field:
            - Nitrogen (N): {npkw_values[0]} mg/kg
            - Phosphorus (P): {npkw_values[1]} mg/kg
            - Potassium (K): {npkw_values[2]} mg/kg
            - Water level in the affected area: {npkw_values[3]}%

            The disease affecting the potato plants has been identified as: **{disease_name}**.

            The normal range for optimal soil health for potato plants is:
            - Nitrogen (N): {self.normal_npkw[0]} mg/kg
            - Phosphorus (P): {self.normal_npkw[1]} mg/kg
            - Potassium (K): {self.normal_npkw[2]} mg/kg
            - Water level: {self.normal_npkw[3]}%

            **Instructions for analysis and suggestions:**
            1. **Analyze NPK and water levels for the diseased area**:
            - Compare the provided NPK values and water levels for the affected area to the normal optimal range for potato plants.
            - Explain if these values are too low or too high and whether they might contribute to the occurrence of the disease. 
            - Describe how deviations in these nutrient levels or water levels could lead to or worsen the specific disease, {disease_name}, in potato plants. Include possible biological or chemical mechanisms if relevant.

            2. **Impact of current nutrient and water levels**:
            - For each nutrient (Nitrogen, Phosphorus, Potassium) and the water level, analyze the possible consequences of the current values. 
            - Explain how each nutrient imbalance or water issue might affect the plant's ability to resist or recover from the disease. Provide clear details for each value:
                - If Nitrogen is too high or low, what could happen to the plant's health and susceptibility to {disease_name}?
                - If Phosphorus is imbalanced, how does it impact disease resistance or root health?
                - If Potassium levels are abnormal, what are the consequences for disease management?
                - If water levels are inappropriate, how could this influence the disease progression or severity?

            3. **Suggest improvements to mitigate the disease**:
            - Based on the analysis, recommend specific actions to improve the soil and water conditions in the affected area.
            - Suggest fertilizers, soil amendments, or treatments that can correct the nutrient imbalances. Mention specific products or ingredients if possible (e.g., urea for nitrogen deficiency or potassium sulfate for potassium deficiency).
            - Provide additional recommendations for managing the disease {disease_name}, such as:
                - Adjustments to irrigation to prevent water stress or overwatering.
                - Organic or chemical treatments to reduce the spread of the disease.
                - Any preventive measures to protect the healthy parts of the field.

            4. **Other suggestions**:
            - If NPK levels are not directly causing the disease, explain other possible factors that could contribute to {disease_name}. 
            - Suggest general soil and crop health improvements that might help the plants recover or resist similar diseases in the future.

            **Final Notes**:
            Please provide the response in a detailed format, with a clear breakdown for each section. Use simple and easy-to-understand language while ensuring that the analysis and suggestions are actionable and thorough. Avoid using any special characters like '*'. Instead, break the response into numbered sections and paragraphs for better clarity.
            And listen write  the response in at least 1000 words
            """
            }
        ]

        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",
        )

        data = chat_completion.choices[0].message.content
        data = data.replace('*', '')
        data = data.replace('**', '')
        return data
