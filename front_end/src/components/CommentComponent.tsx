import { useState } from "react";
import "../App.css";

type CommentContent = {
	type: string;
	content: string;
};

export type VozComment = {
	id: string;
	content: CommentContent[];
	replies?: VozComment[];
	parent?: string;
	user_name: string;
};
export const VozComment = ({ id, content, replies, user_name }: VozComment) => {
	const [isCollapsed, setIsCollapsed] = useState(false);
	const toggleCollapse = () => {
		setIsCollapsed(!isCollapsed);
	};

	return (
		<div className={""}>
			<div className="flex">
				{/* <div className="w-8"> */}
				{/* </div> */}
				<div className={"text-blue-700 font-bold underline"}>
					{user_name}{" "}
					<a href={`https://voz.vn/goto/post?id=${id}`}>| Refer link</a>
				</div>
			</div>
			<div className={"flex"}>
				{isCollapsed ? (
					<>
						<button
							className={
								"basis-[32px] flex-shrink-0 border-l-4 hover:border-slate-500"
							}
							onClick={toggleCollapse}
						></button>
						<button onClick={toggleCollapse}>Mở rộng</button>
					</>
				) : (
					<>
						<button
							className={
								"basis-[32px] flex-shrink-0 border-l-4 hover:border-slate-500"
							}
							onClick={toggleCollapse}
						></button>

						<div>
							<CommentContent content={content} />
							<div>
								{replies?.map((reply) => {
									return <VozComment key={reply.id} {...reply} />;
								})}
							</div>
						</div>
					</>
				)}
			</div>

			<div className={"flex"}></div>
		</div>
	);
};

const CommentContent = ({ content }: { content: CommentContent[] }) => {
	const [isCollapsed, setIsCollapsed] = useState(true);
	return (
		<div>
			{content.map((c) => {
				if (c.type === "blockquote") {
					if (isCollapsed) {
						return (
							<button onClick={() => setIsCollapsed(false)}> [Quote] </button>
						);
					}
					return (
						<>
							<div
								className={"bg-red-400"}
								dangerouslySetInnerHTML={{ __html: c.content }}
							/>
							<button onClick={() => setIsCollapsed(true)}>Thu gọn</button>
						</>
					);
				}
				return <div dangerouslySetInnerHTML={{ __html: c.content }} />;
			})}
		</div>
	);
};
