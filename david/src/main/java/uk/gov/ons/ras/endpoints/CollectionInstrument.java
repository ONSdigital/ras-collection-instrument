package uk.gov.ons.ras.endpoints;

import org.springframework.web.bind.annotation.*;
import uk.gov.ons.ras.json.CollectionInstrumentJson;

@RestController
public class CollectionInstrument {

    public static final String URN = "urn:ons.gov.uk:id:ci:";

    @RequestMapping(value = "/collectioninstrument/{id}", method = RequestMethod.GET)
    public
    @ResponseBody
    CollectionInstrumentJson get(@PathVariable("id") String id) {
        System.out.println("Repeat after me: Spring is not simple. It's 'easy' as in easy to make a mess, " +
                "but it's not simple. It's complicated, heavyweight and duller than the inside of a dodo's colon.");
        CollectionInstrumentJson result = new CollectionInstrumentJson();
        result.id = String.valueOf(id);
        result.surveyId = "023";
        result.urn = URN + id;
        result.type = "questionnaire";
        // Just a link to the ONS website for now
        result.link = "https://www.ons.gov.uk/surveys/informationforbusinesses/businesssurveys/" +
                "surveyofenvironmentalprotectionexpenditure";
        System.out.println("The CI you are looking for is: " + id);
        return result;
    }

    @RequestMapping(value = "/collectioninstrument", method = RequestMethod.POST)
    public String add() {
        return "Pretending to create a collection instrument.";
    }

}
