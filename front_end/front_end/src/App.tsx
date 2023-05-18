import "./App.css";
import { useEffect, useState } from "react";
import { VozComment } from "./components/CommentComponent";

interface ThreadData {
	title: string;
	posts: VozComment[];
}
function App() {
	const [threadData, setThreadData] = useState<ThreadData>();

	const getApiData = async () => {
		const data = await fetch("http://localhost:8001/thread?url=https%3A%2F%2Fvoz.vn%2Ft%2Fjavascript-cho-nguoi-moi-bat-dau.635607%2F", {
			method: "GET",
			headers: {
				"Content-Type": "application/json",
			},
		}).then((response) => response.json());
		setThreadData(data);
	};

	useEffect(() => {
		getApiData();
	}, []);
  
	return (
		<div className="max-w-[800px] m-auto ">
			<h1 className="font-bold text-4xl my-10">{threadData?.title}</h1>

			<div className="p-4 bg-slate-300 rounded-md">
			{threadData?.posts?.map((comment) => (
				<VozComment
					key={comment.id}
					id={comment.id}
					content={comment.content}
          user_name={comment.user_name}
					replies={comment?.replies}
				/>
			))}
			</div>
		</div>
	);
}

export default App;
