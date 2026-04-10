from app.services.ai_service import AIService
from app.utils.logging_config import get_logger


logger = get_logger("app.scripts.test_keyword_ai")


def main() -> None:
    """Run a quick test for AI keyword extraction."""
    service = AIService()

    text = """
    Summary
    This proposal outlines a process to implement a formal pathway for the DAO to issue a “request for information” (RFI) from the Decentraland Foundation.
    Abstract
    The RFI process between Decentraland DAO and the Decentraland Foundation is designed to increase communication and collaboration between both entities. The RFI process will create a mechanism for the DAO to issue a formal request for information from the Foundation within a series of defined categories, which would require a formal statement from the Foundation in response. While the responses will be non-binding, this process will allow for the DAO to more efficiently communicate its interests, and help alleviate information asymmetry between the two core entities of the Decentraland ecosystem.
    Motivation
    Decentraland is a progressively decentralizing ecosystem, managed by two core stakeholders: the Decentraland DAO and the Decentraland Foundation. While both of these entities are themselves made up of a diverse and multi-interested group of stakeholders, a cooperative and structured institutional relationship between the DAO and the Foundation is beneficial, if not necessary to the success of our metaversal "way of life."
    Specification
    This proposal aims to establish a pathway for the DAO to issue a "Request for Information" (RFI) from the Decentraland Foundation via the DAO's governance dApp and/or other complementary tools. A DAO RFI can be on any topic of interest or concern, and if passed, will require a formal statement of response from the Decentraland Foundation. While any response to an RFI will be non-binding, this is an important mechanism for the DAO to communicate its interests and alleviate information "asymmetry" between the Foundation and the Community.
    Channel & Functioning
    The main channel for submitting RFIs and getting responses will be a Category created on the Forum for setting up the ESD.
    Each thread created within the RFI Category will remain open for a continuous period of 45 days for community members to submit their questions through the template form.
    The questions submitted by the community will be ranked based on the number of votes/likes received within a period of 15 days.
    Once the current round of submissions is complete, another round will be opened.
    The Foundation will have a 45 days period to send a response.
    """
    top_k = 8

    try:
        logger.info("AI keyword extraction test started top_k=%s", top_k)
        strict_result = service.extract_keywords_strict(text=text, top_k=top_k)
        #list_result = service.extract_keywords_list(text=text, top_k=top_k)

        print("strict:", strict_result)
        #print("list:", list_result)
        logger.info("AI keyword extraction test completed")
    except Exception:
        logger.exception("AI keyword extraction test failed")
        raise


if __name__ == "__main__":
    main()
