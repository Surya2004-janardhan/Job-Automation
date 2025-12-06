import React, { useRef } from "react";
import { useState, useEffect } from "react";

export default function App() {
  const [count, setCount] = useState(0); //intial value of count is 0
  //    state variable, function to update the state variable
  const [inputtext, setinputtext] = useState("");

  const inputref = useRef(null);
  // useref is used create an obj to persistet trhough the application may be
  // can be used to the keep a focus on something when the componenet mounts
  const [data, setdata] = useState([]);
  useEffect(() => {
    alert("kottav annaw");

    // paina unna fnc exe when this kindha unna array lo avadu marina sarey
    // [] = empty antey only when componenet mounts not everytime
    // kindha unna [] gadi peru dependency array, mottham adey chesthadu maya chusko

    // cleanup fnc exe when component unmounts
    // return () => {
    //   // console.log("clean up");
    //   // alert("clean up maya ");
    // };
  }, [count]);

  useEffect(() => {
    inputref.current.focus(); //simple to doc.getid....
    // it doesnt re render the component when its value changes something like usestate
    // focus on the input box when the component mounts
    // we can access the current value of the ref using inputref.current
    // u can make the func whichn is the callback in useeffect async coz useeffect itself cant be async
    // so we use an inner async fnc and call it inside useeffect
    const fetchdata = async () => {
      const response = await fetch(
        "https://jsonplaceholder.typicode.com/posts"
      );
      const jsondata = await response.json();
      setdata(jsondata);
    };
    // abv is async one and below we call it
    fetchdata();
  }, []);

  return (
    <div>
      <p>Usestate</p>

      <p>
        you clicked this shit {count} times idk just usestate is saying that
      </p>

      <button onClick={() => setCount(count + 1)}>Click to increment</button>
      {/* when clicked it increments the curr count value with cnt+1 usinf setcount usestate fnc */}

      <input
        type="text"
        onChange={(e) => setinputtext(e.target.value)}
        value={inputtext}
        ref={inputref}
        // refering this input dabb to be useref so that focus can be shifted
      />
      <p>You typed this shit {inputtext}</p>

      <h1>Posts</h1>
      <ul>
        {data.map((post) => (
          <li key={post.id}>{post.title}</li>
        ))}
      </ul>
      {/* u type that shit in the textbox it literally uses that typed text under its event values then updates the usestate using the usestate setinputtext fnc */}
    </div>
    // <div>Rey jaffa ga random app component ra daffa--</div>
  );
}
