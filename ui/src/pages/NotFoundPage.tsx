import { Link } from "react-router-dom";
import { PageTitle, buttonSecondary } from "../components";

export function NotFoundPage() {
  return (
    <>
      <PageTitle title="Page not found" sub="This address doesn't match any page." />
      <Link to="/" className={buttonSecondary}>Go to runs</Link>
    </>
  );
}
