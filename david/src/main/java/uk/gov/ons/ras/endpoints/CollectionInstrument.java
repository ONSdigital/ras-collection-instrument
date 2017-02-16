package uk.gov.ons.ras.endpoints;

import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestMapping;

@RestController
public class CollectionInstrument {

    @RequestMapping(value = "/collectioninstrument/{id}", method = RequestMethod.GET)
    public String get(@PathVariable("id") int id) {
        System.out.println("Repeat after me: Spring is not simple. It's 'easy' as in easy to make a mess, " +
                "but it's not simple. It's complicated, heavyweight and duller than the inside of a dodo's colon.");
        return "The CI you are looking for is: " + id;
    }

    @RequestMapping(value = "/collectioninstrument", method = RequestMethod.POST)
    public String add() {
        return "Pretending to create a collection instrument.";
    }

}
