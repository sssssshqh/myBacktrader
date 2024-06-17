import pandas as pd

# List
Person = [ ['Satyam', 21, 'Patna' , 'India' ],
            ['Anurag', 23, 'Delhi' , 'India' ],
            ['Shubham', 27, 'Coimbatore' , 'India' ]]

#Create a DataFrame object
df = pd.DataFrame(Person,
columns = ['Name' , 'Age', 'City' , 'Country'])

# display

# New list for append into df
list = ["Saurabh", 23, "Delhi", "india"]

# using loc methods
df.loc[len(df)] = list

print(df)
