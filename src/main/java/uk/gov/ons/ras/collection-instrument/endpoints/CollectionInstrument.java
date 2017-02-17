package uk.gov.ons.ras.collectionInstrument.endpoints;

import org.springframework.web.bind.annotation.*;
import uk.gov.ons.ras.collectionInstrument.json.CollectionInstrumentJson;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;


@RestController
public class CollectionInstrument {

    @Autowired
    JdbcTemplate jdbcTemplate;

    public static final String URN = "urn:ons.gov.uk:id:ci:";

    @RequestMapping(value = "/collectioninstrument/{id}", method = RequestMethod.GET)
    public
    @ResponseBody
    CollectionInstrumentJson get(@PathVariable("id") String id) {

        /** Uncomment when sql scripts setup is donw
        jdbcTemplate.execute("CREATE TABLE 'customers'( name varchar(40) PRIMARY KEY NOT NULL );")
        jdbcTemplate.execute("DROP TABLE customers"); **/



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
